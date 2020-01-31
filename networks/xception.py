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

# Xception (2016)
# https://arxiv.org/pdf/1610.02357.pdf

import os 
import tensorflow as tf
from tensorflow.keras import layers, Input, Model

def entryFlow(inputs, n_filters,filter_size):
    """ Create the entry flow section
        inputs : input tensor to neural network
    """

    def stem(inputs):
        """ Create the stem entry into the neural network
            inputs : input tensor to neural network
        """
        # Strided convolution - dimensionality reduction
        # Reduce feature maps by 75%
        x = layers.Conv2D(n_filters, (filter_size, filter_size), strides=(2, 2))(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.ReLU()(x)

        # Convolution - dimensionality expansion
        # Double the number of filters
        x = layers.Conv2D(2*n_filters, (filter_size, filter_size), strides=(1, 1))(x)
        x = layers.BatchNormalization()(x)
        x = layers.ReLU()(x)
        return x

    # Create the stem to the neural network
    x = stem(inputs)

    # Create three residual blocks
    for filters in [n_filters, n_filters*2, n_filters]:
        x = projection_block(x, n_filters,filter_size)

    return x

def middleFlow(x,n_filters,filter_size):
    """ Create the middle flow section
        x : input tensor into section
    """
    # Create 8 residual blocks
    for _ in range(8):
        x = residual_block(x, n_filters,filter_size )
    return x

def exitFlow(x, n_classes,filter_size):
    """ Create the exit flow section
        x         : input to the exit flow section
        n_classes : number of output classes
    """
    def classifier(x, n_classes):
        """ The output classifier
            x         : input to the classifier
            n_classes : number of output classes
        """
        # Global Average Pooling will flatten the 10x10 feature maps into 1D
        # feature maps
        x = layers.GlobalAveragePooling2D()(x)
        
        # Fully connected output layer (classification)
        x = layers.Dense(n_classes, activation='softmax')(x)
        return x

    # Remember the input
    shortcut = x

    # Strided convolution to double number of filters in identity link to
    # match output of residual block for the add operation (projection shortcut)
    shortcut = layers.Conv2D(1024, (1, 1), strides=(2, 2),
                             padding='same')(shortcut)
    shortcut = layers.BatchNormalization()(shortcut)

    # First Depthwise Separable Convolution
    # Dimensionality reduction - reduce number of filters
    x = layers.SeparableConv2D(728, (filter_size, filter_size), padding='same')(x)
    x = layers.BatchNormalization()(x)

    # Second Depthwise Separable Convolution
    # Dimensionality restoration
    x = layers.SeparableConv2D(1024, (filter_size, filter_size), padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    # Create pooled feature maps, reduce size by 75%
    x = layers.MaxPooling2D((3, 3), strides=(2, 2), padding='same')(x)

    # Add the projection shortcut to the output of the pooling layer
    x = layers.add([x, shortcut])

    # Third Depthwise Separable Convolution
    x = layers.SeparableConv2D(1556, (filter_size, filter_size), padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    # Fourth Depthwise Separable Convolution
    x = layers.SeparableConv2D(2048, (filter_size, filter_size), padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    # Create classifier section
    x = classifier(x, n_classes)

    return x

def projection_block(x, n_filters,filter_size):
    """ Create a residual block using Depthwise Separable Convolutions with Projection shortcut
        x        : input into residual block
        n_filters: number of filters
    """
    # Remember the input
    shortcut = x
    
    # Strided convolution to double number of filters in identity link to
    # match output of residual block for the add operation (projection shortcut)
    shortcut = layers.Conv2D(n_filters, (1, 1), strides=(2, 2), padding='same')(shortcut)
    shortcut = layers.BatchNormalization()(shortcut)

    # First Depthwise Separable Convolution
    x = layers.SeparableConv2D(n_filters, (filter_size, filter_size), padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    # Second depthwise Separable Convolution
    x = layers.SeparableConv2D(n_filters, (filter_size, filter_size), padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    # Create pooled feature maps, reduce size by 75%
    x = layers.MaxPooling2D((3, 3), strides=(2, 2), padding='same')(x)

    # Add the projection shortcut to the output of the block
    x = layers.add([x, shortcut])

    return x

def residual_block(x, n_filters,filter_size):
    """ Create a residual block using Depthwise Separable Convolutions
        x        : input into residual block
        n_filters: number of filters
    """
    # Remember the input
    shortcut = x

    # First Depthwise Separable Convolution
    x = layers.SeparableConv2D(n_filters, (filter_size, filter_size), padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    # Second depthwise Separable Convolution
    x = layers.SeparableConv2D(n_filters, (filter_size, filter_size), padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    # Third depthwise Separable Convolution
    x = layers.SeparableConv2D(n_filters, (filter_size, filter_size), padding='same')(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)
    
    # Add the identity link to the output of the block
    x = layers.add([x, shortcut])
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
    (entry_flow_n_filters,
    entry_flow_filter_size,
    middle_flow_n_filters,
    middle_flow_filter_size,
    exit_flow_filter_size)=get_configurable_hyperparams()
    # Create the input vector
    inputs = Input(shape=(32, 32, 3))
    # Create entry section
    x = entryFlow(inputs,entry_flow_n_filters, entry_flow_filter_size)
    # Create the middle section
    x = middleFlow(x,middle_flow_n_filters,middle_flow_filter_size)
    # Create the exit section for 1000 classes
    outputs = exitFlow(x, 10,exit_flow_filter_size)

    # Instantiate the model
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
