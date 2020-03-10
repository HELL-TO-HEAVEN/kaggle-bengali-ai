import gc
from typing import List, Callable, AnyStr, Dict, Tuple

import glob2
import pandas as pd
from pandas import DataFrame, Series
from sklearn.model_selection import train_test_split


class DatasetDF():
    def __init__(self,
                 split: float=0.1,
                 apply_X: List[Callable]=[],
                 apply_Y: List[Callable]=[],
                 data_dir='./input/bengaliai-cv19',
                 image_shape=(137,236),
                 data_id=0
    ):
        self.image_shape: Tuple = image_shape

        self.csv_filename = f'{data_dir}/train.csv'
        self.csv_data     = pd.read_csv(self.csv_filename).set_index('image_id', drop=True)

        # There is very little test data, and the csv data is in a different format, so split twice
        self.image_filenames: Dict[AnyStr, List[AnyStr]] = {
            "train": sorted(glob2.glob(f'{data_dir}/train_image_data_{data_id}.parquet')),
            # "test":  sorted(glob2.glob(f'{data_dir}/test_image_data_{data_id}.parquet')),
        }
        self.raw_images: Dict[AnyStr, DataFrame] = {
            'train': pd.concat([pd.read_parquet(file) for file in self.image_filenames['train']])
        }
        self.raw_images['train'], self.raw_images['test']  = train_test_split(self.raw_images['train'], test_size=split*2)
        self.raw_images['test'],  self.raw_images['valid'] = train_test_split(self.raw_images['test'],  test_size=0.5)

        self.X: Dict[AnyStr, Series] = {}
        self.Y: Dict[AnyStr, Series] = {}
        for key in reversed(['train','valid','test']):
            self.X[key] = (
                self.raw_images[key]
                    .drop(columns='image_id', errors='ignore')
                    .values.astype('uint8')
                    .reshape(-1, *self.image_shape, 1)
            )
            if 'image_id' in self.raw_images[key].columns:
                labels = self.raw_images[key]['image_id'].values
                self.Y[key] = self.csv_data.loc[labels]
            else:
                self.Y[key] = pd.Series()

            del self.raw_images[key]; gc.collect()  # Free up memory

        for function in apply_X:
            for key in self.X:
                self.X[key] = self.X[key].apply(function)

        for function in apply_Y:
            for key in self.Y:
                self.X[key] = self.X[key].apply(function)

    def epoc_size(self):
        return self.X['train'].shape[0]

    def input_shape(self):
        return self.X['train'].shape[1:]

    def output_shape(self):
        return self.Y['train'].shape[-1]


if __name__ == '__main__':
    # NOTE: loading all datasets exceeds 12GB RAM and crashes Python (on 16GB RAM machine)
    for data_id in range(0,4):
        dataset = DatasetDF(data_id=data_id)
        print(f"{data_id} dataset.image_filenames", dataset.image_filenames)
        print(f"{data_id} dataset.raw_images",      { key: df.shape for key, df in dataset.raw_images.items()})
        print(f"{data_id} dataset.X",               { key: df.shape for key, df in dataset.X.items()         })
        print(f"{data_id} dataset.Y",               { key: df.shape for key, df in dataset.Y.items()         })
        print(f"{data_id} dataset.image_shape", dataset.image_shape)