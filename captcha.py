import pickle
from queue import Queue

import cv2
import numpy as np


class NeuralNetwork:
    def __init__(self):
        data = pickle.load(open('./model.pck', 'rb'))
        self.weights = data[0]
        self.biases = data[1]

    @staticmethod
    def sigmoid(x):
        return 1 / (1 + np.exp(-x))

    def guess(self, img):
        x = (1 - img/255).reshape((150, 1))
        activation = x
        for b, w in zip(self.biases, self.weights):
            activation = self.sigmoid((w @ activation) + b)
        result = [activation[i][0] for i in range(10)]
        return result.index(max(result))


def dfs(mask, x, y, task):
    if 0 <= x < mask.shape[0] and 0 <= y < mask.shape[1] and not mask[x][y]:
        mask[x, y] = 1
        task.put((x, y))
        for way in ((-1, 0), (0, 1), (0, -1), (1, 0)):
            dfs(mask, x + way[0], y + way[1], task)


def guess(img):
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)[:27, :67]
    img = cv2.threshold(img, 180, 255, cv2.THRESH_BINARY)[1]
    mask = np.array(np.where(cv2.GaussianBlur(img, (3, 5), 0) > 210, 255, 0), dtype=np.uint8)
    count, cuts = 0, []
    for i in range(mask.shape[0]):
        for j in range(mask.shape[1]):
            area = Queue()
            min_x, max_x, min_y, max_y = 1 << 20, -1, 1 << 20, -1
            dfs(mask, i, j, area)
            if 20 < area.qsize() < 150:
                count += 1
                while not area.empty():
                    tmp = area.get()
                    min_x, max_x, min_y, max_y = min(min_x, tmp[0]), max(max_x, tmp[0]), min(min_y, tmp[1]), max(max_y, tmp[1])
                cuts.append((min_x, max_x+1, min_y, max_y+1))
            else:
                while not area.empty():
                    mask[area.get()] = 255
    img[np.where(mask != 1)] = 255
    cuts.sort(key=lambda s: s[2])
    network = NeuralNetwork()
    result = ''
    if count == 4:
        for i, ss in enumerate(cuts):
            digit = cv2.resize(img[ss[0]:ss[1], ss[2]:ss[3]], (2*(ss[3]-ss[2]), 2*(ss[1]-ss[0])))
            digit = cv2.resize(digit, (ss[3]-ss[2], ss[1]-ss[0]))
            template = np.full((15, 10), 255, dtype=np.uint8)
            if 3 * digit.shape[1] > 2 * digit.shape[0]:
                digit = cv2.resize(
                    digit, (10, int(10 * digit.shape[0] / digit.shape[1])), interpolation=cv2.INTER_LINEAR_EXACT
                )
                dy = int((15 - digit.shape[0]) / 2)
                template[dy:dy+digit.shape[0], :] = digit
            else:
                digit = cv2.resize(
                    digit, (int(15 * digit.shape[1] / digit.shape[0]), 15), interpolation=cv2.INTER_LINEAR_EXACT
                )
                dx = int((10 - digit.shape[1]) / 2)
                template[:, dx:dx+digit.shape[1]] = digit
            result += str(network.guess(template))
        return result
    return '0000'
