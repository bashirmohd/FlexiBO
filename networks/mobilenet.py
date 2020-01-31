# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# MobileNet 224 (2017)
# Paper: https://arxiv.org/pdf/1704.04861.pdf
import os 
import tensorflow as tf
from tensorflow.keras import layers, Input, Model

def stem(inputs, alpha, n_filters, 
        filter_size):
    """ Construct the stem group
        inputs : input tensor
        alpha  : width multiplier
    """
    # Convolutional block
    x = layers.ZeroPadding2D(padding=((0, 1), (0, 1)))(inputs)
    x = layers.Conv2D(n_filters, (filter_size, filter_size), strides=(2, 2), padding='valid')(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    # Depthwise Separable Convolution Block
    x = depthwise_block(x, 64, alpha, (1, 1))
    return x

def classifier(x, alpha, dropout, n_classes):
    """ Construct the classifier group
        x         : input to the classifier
        alpha     : width multiplier
        dropout   : dropout percentage
        n_classes : number of output classes
    """

    # Flatten the feature maps into 1D feature maps (?, N)
    x = layers.GlobalAveragePooling2D()(x)

    # Reshape the feature maps to (?, 1, 1, 1024)
    shape = (1, 1, int(1024 * alpha))
    x = layers.Reshape(shape)(x)
    # Perform dropout for preventing overfitting
    x = layers.Dropout(dropout)(x)

    # Use convolution for classifying (emulates a fully connected layer)
    x = layers.Conv2D(n_classes, (1, 1), padding='same')(x)
    x = layers.Activation('softmax')(x)
    # Reshape the resulting output to 1D vector of number of classes
    x = layers.Reshape((n_classes, ))(x)

    return x

def depthwise_block(x, n_filters, alpha, strides):
    """ Construct a Depthwise Separable Convolution block
        x         : input to the block
        n_filters : number of filters
        alpha     : width multiplier
        strides   : strides
    """
    # Apply the width filter to the number of feature maps
    filters = int(n_filters * alpha)

    # Strided convolution to match number of filters
    if strides == (2, 2):
        x = layers.ZeroPadding2D(padding=((0, 1), (0, 1)))(x)
        padding = 'valid'
    else:
        padding = 'same'

    # Depthwise Convolution
    x = layers.DepthwiseConv2D((3, 3), strides, padding=padding)(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    # Pointwise Convolution
    x = layers.Conv2D(filters, (1, 1), strides=(1, 1), padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)
    return x

def get_configurable_hyperparams():
    """This function is used to ge the configurable hyperparameters 
    """
    import yaml
    with open("cur_config.yaml") as fp:
            cur_cfg=yaml.load(fp)
    return (cur_cfg["cur_conf"][0], cur_cfg["cur_conf"][1], cur_cfg["cur_conf"][2],
            cur_cfg["cur_conf"][3], cur_cfg["cur_conf"][4])

def get_data():
    """This function is used to get train and test data
    """
    from tensorflow.keras.datasets import cifar10 
    import numpy as np
    (x_train, y_train), (x_test, y_test) = cifar10.load_data() 
    x_train = (x_train / 255.0).astype(np.float32) 
    x_test = (x_test / 255.0).astype(np.float32) 
    return x_train, y_train, x_test, y_test

if __name__=="__main__":
    
    # get configurable hyperparams
    (stem_n_filters,
    stem_filter_size
    depthwise_block1_n_filters,
    depthwise_block2_n_filters,
    depthwise_block3_n_filters,
    depthwise_block4_n_filters,)=get_configurable_hyperparams()

    alpha      = 1    # width multiplier
    dropout    = 0.5  # dropout percentage
    n_classes = 1000 # number of classes

    inputs = Input(shape=(224, 224, 3))

    # Create the stem group
    x = stem(inputs, alpha, stem_n_filters, 
             stem_filter_size)    

    # First Depth wise Separable Convolution Group
    # Strided convolution - feature map size reduction
    x = depthwise_block(x, depthwise_block1_n_filters, alpha, strides=(2, 2))
    x = depthwise_block(x, depthwise_block1_n_filters, alpha, strides=(1, 1))

    # Second Depthwise Separable Convolution Group
    # Strided convolution - feature map size reduction
    x = depthwise_block(x, depthwise_block2_n_filters, alpha, strides=(2, 2))
    x = depthwise_block(x, depthwise_block2_n_filters, alpha, strides=(1, 1))

    # Third Depthwise Separable Convolution Group
    # Strided convolution - feature map size reduction
    x = depthwise_block(x, depthwise_block3_n_filters, alpha, strides=(2, 2))
    for _ in range(5):
        x = depthwise_block(x, depthwise_block3_n_filters, alpha, strides=(1, 1))

    # Fourth Depthwise Separable Convolution Group
    # Strided convolution - feature map size reduction
    x = depthwise_block(x, depthwise_block4_n_filters, alpha, strides=(2, 2))
    x = depthwise_block(x, depthwise_block4_n_filters, alpha, strides=(1, 1))

    # Create the classifier
    outputs = classifier(x, alpha, dropout, n_classes)

    # Instantiate the Model
    model = Model(inputs, outputs)
    model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['acc'])
    model.summary()

    xtrain, ytrain, x_test, y_test=get_data()    
    # train model
    model.fit(x_train, y_train, epochs=10, 
              batch_size=32, validation_split=0.1, verbose=1)
    
    # save model
    fmodel=os.path.join(os.get_cwd(),"model.h5") 
    model.save(fmodel)
