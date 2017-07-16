from __future__ import print_function

import numpy as np
from sklearn.decomposition import PCA
from sklearn import metrics
from matplotlib import pyplot as plt
import pickle
import re    



import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.preprocessing.text import Tokenizer
from keras.layers import Embedding
from keras.layers import Conv1D, GlobalAveragePooling1D, MaxPooling1D

from create_dataset_thai import content2index, load_dataset, load_dataset_unknown

MAX_WORDS = 5003

def plotPCA2d(X, label_list, num_classes):
	estimator = PCA(n_components=2)
	Xpca = estimator.fit_transform(X)	
	assert np.shape(Xpca) == (np.shape(X)[0], 2)
	
	colors = ['red', 'green','blue', 'black', ]
	for label in range(0, num_classes): # 0 to 3
		label_list = np.array(label_list)	# convert to array with numpy
		AB = Xpca[np.where(label_list == label)[0]]	
		# seperate to a, b component 
		a = AB[:, 0]	
		b = AB[:, 1]
		plt.scatter(a, b, c=colors[label])
	plt.legend(np.arange(0,num_classes), loc='upper right')
	plt.xlabel('First Principal Component')
	plt.ylabel('Second Principal Component')
	plt.show()

def preprocessing(X_train, X_test, Y_train, Y_test, num_classes):
	print('Before convert of sequence words to binary matrix...')
	print('X_train shape:', np.shape(X_train))
	print('X_test shape:', np.shape(X_test))	
	
	print('Convert sequences of words (index) to binary matrix')	
	tokenizer = Tokenizer(num_words=MAX_WORDS)
	# Return: numpy array of shape (len(sequences), num_words).
	X_train = tokenizer.sequences_to_matrix(X_train, mode='binary')
	X_test = tokenizer.sequences_to_matrix(X_test, mode='binary')
	print('X_train shape:', X_train.shape)
	print('X_test shape:', X_test.shape)	

	print('Convert class label (integers vector) to binary class matrix')
	Y_train = keras.utils.to_categorical(Y_train, num_classes)
	Y_test = keras.utils.to_categorical(Y_test, num_classes)
	print('Y_train shape:', Y_train.shape)
	print('Y_test shape:', Y_test.shape)
	return X_train, X_test, Y_train, Y_test

# Multilayer Perceptron (MLP)
def build_MLP(num_classes):
	model = Sequential()
	model.add(Dense(512, input_shape=(MAX_WORDS,)))
	model.add(Activation('relu'))
	model.add(Dropout(0.5))
	model.add(Dense(num_classes))
	model.add(Activation('softmax'))
	model.compile(loss='categorical_crossentropy',
			  optimizer='adam',
			  metrics=['accuracy'])
	return model

# Convolutional Neural Networks (CNN)
def build_CNN(num_classes):
	model = Sequential()	
	model.add(Conv1D(filters=64, kernel_size=3, padding="same", activation='relu', input_shape=(MAX_WORDS, 1 )))
	model.add(Conv1D(filters=64, kernel_size=3, padding="same", activation='relu'))
	model.add(MaxPooling1D(3))
	model.add(Conv1D(filters=128, kernel_size=3, padding="same", activation='relu'))
	model.add(Conv1D(filters=128, kernel_size=3, padding="same", activation='relu'))
	#model.add(GlobalAveragePooling1D())
	model.add(Flatten())
	model.add(Dense(units=10))
	model.add(Dropout(0.5))
	model.add(Dense(units=num_classes, activation='softmax'))
	model.compile(loss='categorical_crossentropy',
			  optimizer='adam',
			  metrics=['accuracy'])
	return model

def decode(Y_binary):
	# np.argmax: Returns the indices of the maximum values along an axis.	
	return np.array( [ np.argmax(list) for list in Y_binary] )
	
def train(model, X_train, X_test, Y_train, Y_test ):
	model.fit(X_train, Y_train,
					batch_size=32,
					epochs=5,
					verbose=0,
					validation_split=0.1)
	score = model.evaluate(X_test, Y_test,
					   batch_size=32, verbose=0)
	print('Test %s: %.4f' % (model.metrics_names[0], score[0]))
	print('Test %s: %.4f %%' % (model.metrics_names[1], score[1]*100))
	
	Ypredicted = model.predict(X_test, verbose=0)
	Yexpected = decode(Y_test)
	Ypredicted = decode(Ypredicted)
	print("Classification report")
	print(metrics.classification_report( Yexpected, Ypredicted))
	
def test(model):		
	# label 0: 	"article", label 1: "encyclopedia", label 2: "news", label 4: "novel"
	label = ["Article", "Encyclopedia", "News", "Novel"]	
	# I used this text file for test from : https://www.nectec.or.th/corpus/index.php?league=pm		
	file_name = "TEST_NOVEL.txt.p"
	contentList = load_dataset_unknown(file_name)
	# subsample to small
	contentList = [contentList] # input shape to the model is [1, number word]
	
	# Convert sequences of words (index) to binary matrix
	tokenizer = Tokenizer(num_words=MAX_WORDS)
	content_binary = tokenizer.sequences_to_matrix(contentList, mode='binary')
	predict = model.predict(content_binary) 	# output shape is (1, number label)
	index_label = np.argmax(predict[0])
	print("Predict: this file '%s' is '%s'" % (file_name , label[index_label])) 	
	
if __name__ == "__main__":	
	print('Loading data...')
	X_train, X_test, Y_train, Y_test = load_dataset()
	num_classes = np.max(Y_train) + 1
	print("Total class:", num_classes)

	print('Convert all data to binary vectorizing data')
	X_trainNew, X_testNew, Y_trainNew, Y_testNew = preprocessing(X_train, X_test, Y_train, Y_test, num_classes)
	print("Plot graph 2D (Principal component analysis (PCA))")
	plotPCA2d(X_trainNew, Y_train , num_classes) # use Y_train without vectorized

	print('\n+++++ Example: Building Multilayer Perceptron (MLP)  +++++')
	model_MPL = build_MLP(num_classes)
	print(model_MPL.summary())
	print('Training with MPL model...')
	train(model_MPL, X_trainNew, X_testNew, Y_trainNew, Y_testNew)
	
	print('\n+++++ Example: Convolutional Neural Networks (CNN) with Convolution1D +++++')
	model_CNN = build_CNN(num_classes)
	print(model_CNN.summary())
	print('Training with CNN model ...take a minute')	
	# For Convolutional 1D only, I reshaped input to (batch_size, steps, input_dim) 
	XX_trainNew = np.reshape(X_trainNew, (-1, MAX_WORDS, 1))
	XX_testNew = np.reshape(X_testNew, (-1, MAX_WORDS, 1))
	# Training CNN is very slow
	train(model_CNN, XX_trainNew , XX_testNew, Y_trainNew, Y_testNew)
	
	# +++++++++++++ test a data that never found ++++++++++++++++
	print('Testinng data that never found')		
	test(model_MPL)
	test(model_CNN)
	
	