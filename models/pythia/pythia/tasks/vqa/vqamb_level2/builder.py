from pythia.common.registry import registry
from pythia.tasks.base_dataset_builder import BaseDatasetBuilder
from pythia.tasks.vqa.vqamb_level2.dataset import VQAmb_Level2Dataset

import json
import random
import copy

@registry.register_builder("vqamb_level2")
class VQAmb_Level2Builder(BaseDatasetBuilder):

	def __init__(self):
		super().__init__("vqamb_level2")
		self.writer = registry.get("writer")

		self.dataset_class = VQAmb_Level2Dataset

	# Divides dataset into train, val, and test
	def get_dataset_div(self, vqamb_img, dataset_type, config):
		imgs_length = len(vqamb_img)
		train_cutoff = int(round(0.8 * imgs_length))
		val_cutoff = train_cutoff + int(round(0.1 * imgs_length))
		
		keys = list(vqamb_img.keys())
		random.Random(4).shuffle(keys)
		
		train_set, val_set, test_set = [], [], []

		for cnt, key in enumerate(keys):
			if cnt <= train_cutoff:
				train_set.extend(vqamb_img[key])
			elif cnt <= val_cutoff:
				val_set.extend(vqamb_img[key])
			else:
				test_set.extend(vqamb_img[key])

		# filter train, val, test if desired
		# test_set = self.filter_dataset(test_set)
		# train_set, val_set, test_set = self.filter_dataset(train_set), self.filter_dataset(val_set), self.filter_dataset(test_set)
		print(len(train_set))
		div = {'train': train_set, 'val': val_set, 'test': test_set} # Change 'val'->val set
		return div

	def get_dataset_div_marked(self, vqamb_img, dataset_type, config, relax=False):
		train = []
		val = []
		test = []
		for img_id in vqamb_img:
			for qa in vqamb_img[img_id]:
				if relax:
					qa['pt_question'] = self.relax_question(qa['pt_question'])
				if qa['div'] in ['train', 'trainadd']: 
					train.append(qa)
				elif qa['div'] == 'val': 
					val.append(qa)
				else: 
					test.append(qa)

		print(len(train))
		div = {'train': train, 'val': val, 'test': test}
		return div

	def relax_question(self, question):
		words = question.split()
		del words[4]
		q_new = ' '.join(words)
		return q_new

	def filter_dataset(self, pt_dataset):
		filtered_dataset = []
		for qa in pt_dataset:
			if 'qtype' in qa and qa['qtype'] == 'howmany':
				filtered_dataset.append(qa)
		return filtered_dataset
			
		# Intended for downloading files and actually "building" the dataset
	def _build(self, dataset_type, config):

		self.img_folder = ''
		
		data_folder = ''
		self.detectron_folder = data_folder + config.feat_folder + '/'
		
		self.context_folder = data_folder + config.context_feat_folder + '/'

		vqamb_path = ''
		with open(vqamb_path, 'r') as f:
			vqamb_img = json.load(f)
			
		self.div = self.get_dataset_div_marked(vqamb_img, dataset_type, config)

	def _load(self, dataset_type, config, *args, **kwargs):
		self.dataset = VQAmb_Level2Dataset(
			dataset_type, config, img_folder = self.img_folder,
			detectron_folder = self.detectron_folder, context_folder=self.context_folder, vqamb_div=self.div
		)

		return self.dataset

	def update_registry_for_model(self, config):
		# Register vocab (question and answer) sizes to registry for easy access to models.
		registry.register(
			self.dataset_name + "_text_vocab_size",
			self.dataset.text_processor.get_vocab_size(),
		)
		
		registry.register(
			self.dataset_name + "_num_final_outputs",
			self.dataset.answer_processor.get_vocab_size()-1,
		)
