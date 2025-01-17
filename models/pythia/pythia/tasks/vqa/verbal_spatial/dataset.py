import json
import random
random.seed(4)

import torch
from torchvision import transforms

from pythia.common.registry import registry
from pythia.common.sample import Sample
from pythia.tasks.base_dataset import BaseDataset
from pythia.tasks.features_dataset import FeaturesDataset
from pythia.utils.text_utils import tokenize

import sys
# from detectron import PythiaDetectron

import copy
from PIL import Image

class Verbal_SpatialDataset(BaseDataset):

	def __init__(self, dataset_type, config, img_folder, detectron_folder, 
		     context_folder, vqamb_div, *args, **kwargs):
		super().__init__("verbal_spatial", dataset_type, config)

		self.dataset_type = dataset_type
		self.img_folder = img_folder
		self.detectron_folder = detectron_folder
		self.context_folder = context_folder
		self.vqamb_data = vqamb_div[dataset_type]

		# self.detectron = PythiaDetectron()

		# hardcode these for now, can move them out later
		self.target_image_size = (448, 448)
		self.channel_mean = [0.485, 0.456, 0.406]
		self.channel_std = [0.229, 0.224, 0.225]

		self.cnt = 0
	
	def __len__(self):
		return len(self.vqamb_data)

	# Image transform for detectron - used if we don't precompute features
	def _image_transform(self, img):
		pass

	def get_item(self, idx):

		data = self.vqamb_data[idx]

		current_sample = Sample()

		# store queston and image id
		current_sample.img_id = data['id']
		current_sample.qa_id = data['qa_id']

		# process question
		question = data["question"]
		tokens = tokenize(question, remove=["?"], keep=["'s"])

		processed = self.text_processor({"tokens": tokens})
		current_sample.text = processed["text"]

		# process answers
		processed = self.answer_processor({"answers": [data['answer']]})
		current_sample.answers = processed["answers"]
		current_sample.targets = processed["answers_scores"][1:] # remove unknown index
		# Detectron features ----------------
		# TODO: read in detectron image instead if detectron is to be built
		detectron_path = self.detectron_folder + str(data['id'])
		if self.config.spatial:
			point = data['point']
			# current_sample.point = point
			detectron_path += ',' + str(point['x']) + ',' + str(point['y'])
		detectron_path += '.pt'
		
		detectron_feat = torch.load(detectron_path, map_location=torch.device('cpu'))

		# Pad features to fixed length
		if self.config.pad_detectron:
			if detectron_feat.shape[0] > 100:
				detectron_feat = detectron_feat[:100]
			elif detectron_feat.shape[0] < 100:
				pad = torch.zeros(100 - detectron_feat.shape[0], detectron_feat.shape[1])
				detectron_feat = torch.cat([detectron_feat, pad], dim=0)

		current_sample.image_feature_0 = detectron_feat
		# ---------------------------------------------

		return current_sample
		
		
