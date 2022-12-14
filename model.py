import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
import math
import utils

class feature_extractor(nn.Module):
    def __init__(self):
        super(feature_extractor, self).__init__()
        vgg16 = models.vgg16(pretrained=True)
        # vgg16.load_state_dict(torch.load('vgg16.pth'))
        self.feature_ex = nn.Sequential(*list(vgg16.children())[:-1])
    def forward(self, input):
        x = input.squeeze(0)
        feature = self.feature_ex(x)
        feature = feature.view(feature.size(0), -1)
        return feature

class class_predictor(nn.Module):
    def __init__(self, LABEL_NUM_CLASSES):
        super(class_predictor, self).__init__()
        # reduce feature dimension
        self.feature_extractor_2 = nn.Sequential(
            nn.Linear(in_features=25088, out_features=2048),
            nn.ReLU(),
            nn.Linear(in_features=2048, out_features=512),
            nn.ReLU()
        )
        # attention network
        self.attention = nn.Sequential(
            nn.Linear(512, 128),
            nn.Tanh(),
            nn.Linear(128, 1)
        )
        # class predictor
        self.classifier = nn.Sequential(
            nn.Linear(512, LABEL_NUM_CLASSES),
        )

    def forward(self, input):
        x = input.squeeze(0)
        H = self.feature_extractor_2(x)
        A = self.attention(H)
        A = torch.transpose(A, 1, 0)
        A = F.softmax(A, dim=1)
        M = torch.mm(A, H)  # KxL
        class_prob = self.classifier(M)
        class_sigmoid = torch.sigmoid(class_prob)
        # class_softmax = F.softmax(class_prob, dim=1)
        # class_hat = int(torch.argmax(class_softmax, 1))
        return class_sigmoid, A
        # return class_prob, class_hat, A

class EM_MIL(nn.Module):
    def __init__(self, feature_ex, class_predictor):
        super(EM_MIL, self).__init__()
        self.feature_extractor = feature_ex
        self.class_predictor = class_predictor

    def forward(self, input):
        x = input.squeeze(0)
        # extract feature vectors
        features = self.feature_extractor(x)
        # class prediction
        class_sigmoid, A = self.class_predictor(features)
        # class_prob, class_hat, A = self.class_predictor(features)
        return class_sigmoid, A
