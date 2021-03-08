import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers
from tensorflow import keras
import matplotlib.pyplot as plt

def Train(epochs, restore:bool):
    
    #Training data
    dataset = pd.read_csv("Data/dataset.csv").apply(pd.to_numeric)
    labels = dataset.pop("Position").to_numpy()
    dataset.pop("0")
    dataset = dataset.to_numpy()
    
    #Validation data
    v_x = pd.read_csv("Data/validationdataset.csv").apply(pd.to_numeric)
    v_y = v_x.pop("Position").to_numpy()
    v_x.pop("0")
    v_x = v_x.to_numpy()


    model = tf.keras.models.Sequential([
        keras.layers.Dense(400, activation="sigmoid"),
        keras.layers.Dense(400, activation="sigmoid"),
        keras.layers.Dense(400, activation="sigmoid"),
        tf.keras.layers.Dropout(0.2),
        keras.layers.Dense(200, activation="sigmoid"),
        keras.layers.Dense(100, activation="sigmoid"),
        keras.layers.Dense(50, activation="sigmoid"),
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

    #Adjust learning rate
    lr_callback = tf.keras.callbacks.ReduceLROnPlateau(
        monitor="loss",
        factor=0.1,
        patience=3,
        verbose=1,
        mode="auto",
        min_delta=0.0001,
        cooldown=1,
        min_lr=0,
    )

    print("Fitting")
    history = model.fit(dataset, labels, epochs=epochs, callbacks=[cp_callback, lr_callback], validation_data=(v_x,v_y))

    # summarize history for accuracy
    plt.plot(history.history['acc'])
    plt.plot(history.history['val_acc'])
    plt.title('model accuracy')
    plt.ylabel('accuracy')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    plt.show()
    # summarize history for loss
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('model loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    plt.show()
    
    print(model.evaluate(v_x,v_y))
    model.save("model")

if __name__ == '__main__':
    Train(5, True)