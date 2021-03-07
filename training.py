import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers
from tensorflow import keras
import matplotlib.pyplot as plt

def Train(epochs, restore:bool):
    dataset = pd.read_csv("Data/dataset.csv").apply(pd.to_numeric)
    labels = dataset.pop("Position").to_numpy()
    dataset.pop("0")
    dataset = dataset.to_numpy()



    model = tf.keras.models.Sequential([
        keras.layers.Dense(400, activation="sigmoid"),
        keras.layers.Dense(600, activation="sigmoid"),
        tf.keras.layers.Dropout(0.2),
        keras.layers.Dense(600, activation="sigmoid"),
        keras.layers.Dense(400, activation="sigmoid"),
        keras.layers.Dense(100, activation="sigmoid"),
        keras.layers.Dense(3, activation="softmax")
    ])

    print("Compiling model")
    model.compile(optimizer='adam',
                  loss=tf.keras.losses.CategoricalCrossentropy(),
                  metrics=['accuracy'])

    #Checkpointing
    checkpoint_path = "checkpoints/cp.ckpt"
    cp_callback = tf.keras.callbacks.ModelCheckpoint(filepath=checkpoint_path, save_weights_only=True)
    
    #restore checkpoint
    if(restore):
        model.load_weights(checkpoint_path)


    print("Fitting")
    history = model.fit(dataset, labels, epochs=epochs, callbacks=[cp_callback])

    history_dict = history.history
    history_dict.keys()

    acc = history_dict['binary_accuracy']
    val_acc = history_dict['val_binary_accuracy']
    loss = history_dict['loss']
    val_loss = history_dict['val_loss']

    epochs = range(1, len(acc) + 1)

    # "bo" is for "blue dot"
    plt.plot(epochs, loss, 'bo', label='Training loss')
    # b is for "solid blue line"
    plt.plot(epochs, val_loss, 'b', label='Validation loss')
    plt.title('Training and validation loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()

    plt.show()


if __name__ == '__main__':
    Train(50, False)