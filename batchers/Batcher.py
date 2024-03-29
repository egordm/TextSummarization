import os
import pickle
import numpy as np
import datasets.embeddings as embeddings
from datasets.embeddings import get_embeddings, get_embedding_matrix
from datasets.text_utils import *
from datasets.utils import *

class Batcher:
    threshold = 20

    def __init__(self, inputs, targets, batch_size=20, path=None):
        print('Initializing Batcher')

        self.batch_size = batch_size
        self.cursor = 0

        if path is not None:
            try:
                self.load_data(path)
                return
            except:
                print('Error loading existing vocab & embeddings')

        self._create_embeddings(inputs, targets)
        self._process_data(inputs, targets)
        self.save_data(path)

    def _create_embeddings(self, inputs, targets):
        word_counts = {}
        count_words(word_counts, inputs)
        count_words(word_counts, targets)
        print("Vocabulary size:", len(word_counts))

        embedding_keys = get_embeddings()

        self.vocab_id = create_dictionary(word_counts, embedding_keys)
        self.id_vocab = inverse_dictionary(self.vocab_id)

        self.embeddings = get_embedding_matrix(self.vocab_id)
        embeddings._embeddings = None
        print("Embedding size:", len(self.embeddings))

    def _process_data(self, inputs, targets):
        input_indexes = convert_to_ints(inputs, self.vocab_id, eos=True)
        target_indexes = convert_to_ints(targets, self.vocab_id)

        lengths_inputs = create_lengths(input_indexes)
        lengths_targets = create_lengths(target_indexes)

        # Analyze lenghth
        # print("Inputs:")
        # print(lengths_inputs.describe())
        # print("Targets:")
        # print(lengths_targets.describe())

        self.inputs = []
        self.targets = []

        max_inputs_length = 600
        min_length = 16
        unk_input_limit = 5
        unk_target_limit = 2

        for length in range(min(lengths_inputs.counts), max_inputs_length):
            for count, words in enumerate(target_indexes):
                if len(target_indexes[count]) < min_length or len(target_indexes[count]) > max_inputs_length: continue
                if len(input_indexes[count]) < min_length: continue
                if unk_counter(target_indexes[count], self.vocab_id) > unk_target_limit: continue
                if unk_counter(input_indexes[count], self.vocab_id) > unk_input_limit: continue
                if length != len(target_indexes[count]): continue
                self.inputs.append(input_indexes[count])
                self.targets.append(target_indexes[count])

        print('# Inputs: {}, # Targets {}'.format(len(self.inputs), len(self.targets)))

    def get_batch(self):
        if self.cursor >= len(self.inputs) - self.batch_size: self.cursor = 0
        start = self.cursor
        inputs = self.inputs[start:start + self.batch_size]
        targets = self.targets[start:start + self.batch_size]

        inputs = np.array(pad_sentence_batch(inputs, self.vocab_id))
        targets = np.array(pad_sentence_batch(targets, self.vocab_id))

        input_lengths = []
        for input in inputs:
            input_lengths.append(len(input))

        target_lengths = []
        for target in targets:
            target_lengths.append(len(target))

        self.cursor += self.batch_size
        return inputs, targets, input_lengths, target_lengths

    def save_data(self, path):
        save_data(self.embeddings, '{}/embeddings.txt'.format(path))
        save_data(self.vocab_id, '{}/vocabulary.txt'.format(path))
        save_data((self.inputs, self.targets), '{}/data.txt'.format(path))

    def load_data(self, path):
        self.embeddings = load_data('{}/embeddings.txt'.format(path))
        self.vocab_id = load_data('{}/vocabulary.txt'.format(path))
        self.id_vocab = inverse_dictionary(self.vocab_id)
        self.inputs, self.targets = load_data('{}/data.txt'.format(path))
        print("Vocabulary size:", len(self.vocab_id))
        print("Embedding size:", len(self.embeddings))
        print('# Inputs: {}, # Targets {}'.format(len(self.inputs), len(self.targets)))
        print("Loaded saved batcher data")
