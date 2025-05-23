from . import SentenceEvaluator
import torch
from torch.utils.data import DataLoader
import logging
from ..util import batch_to_device
import os
import csv
import sklearn
import numpy as np

logger = logging.getLogger(__name__)

def Accuracy(y_true, y_pred):
    count = 0
    for i in range(y_true.shape[0]):
        p = sum(np.logical_and(y_true[i], y_pred[i]))
        q = sum(np.logical_or(y_true[i], y_pred[i]))
        count += p / q
    return count / y_true.shape[0]

class MultiLabelAccuracyEvaluator(SentenceEvaluator):
    """
    Evaluate a model based on its accuracy on a labeled dataset

    This requires a model with LossFunction.SOFTMAX

    The results are written in a CSV. If a CSV already exists, then values are appended.
    """

    def __init__(self, dataloader: DataLoader, name: str = "", softmax_model = None, write_csv: bool = True):
        """
        Constructs an evaluator for the given dataset

        :param dataloader:
            the data for the evaluation
        """
        self.dataloader = dataloader
        self.name = name
        self.softmax_model = softmax_model

        if name:
            name = "_"+name

        self.write_csv = write_csv
        self.csv_file = "accuracy_evaluation"+name+"_results.csv"
        self.csv_headers = ["epoch", "steps", "accuracy"]

    def __call__(self, model, output_path: str = None, epoch: int = -1, steps: int = -1) -> float:
        model.eval()
        total = 0
        correct = 0
        y_pred = []
        y_true = []
        result = []
        if epoch != -1:
            if steps == -1:
                out_txt = " after epoch {}:".format(epoch)
            else:
                out_txt = " in epoch {} after {} steps:".format(epoch, steps)
        else:
            out_txt = ":"

        logger.info("Evaluation on the "+self.name+" dataset"+out_txt)
        self.dataloader.collate_fn = model.smart_batching_collate
        for step, batch in enumerate(self.dataloader):
            features, label_ids = batch
            for idx in range(len(features)):
                features[idx] = batch_to_device(features[idx], model.device)
            label_ids = label_ids.to(model.device)
            with torch.no_grad():
                _, prediction = self.softmax_model(features, labels=None)


            total += prediction.size(0)
            pred = (prediction>0.5).int()
            label = label_ids.int()
            result.append(Accuracy(label.cpu().numpy(), pred.cpu().numpy()))

        accuracy = sum(result)/len(result)

        logger.info("Accuracy: {:.4f}\n".format(accuracy))

        # if output_path is not None and self.write_csv:
        #     csv_path = os.path.join(output_path, self.csv_file)
        #     if not os.path.isfile(csv_path):
        #         with open(csv_path, newline='', mode="w", encoding="utf-8") as f:
        #             writer = csv.writer(f)
        #             writer.writerow(self.csv_headers)
        #             writer.writerow([epoch, steps, accuracy])
        #     else:
        #         with open(csv_path, newline='', mode="a", encoding="utf-8") as f:
        #             writer = csv.writer(f)
        #             writer.writerow([epoch, steps, accuracy])

        return accuracy
