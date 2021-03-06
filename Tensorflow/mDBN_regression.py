from __future__ import print_function, division
from sklearn.datasets import load_boston
from sklearn.cross_validation import train_test_split
from sklearn.metrics.regression import r2_score, mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA

from tf_models import *

import sys
import numpy
import timeit

from dataset_location import *


def load_data(dataset, pca=2):
    """ The load dataset function
    
    This function covers for singular dataset
    (either DNA Methylation, Gene Expression, or miRNA Expression)
    for survival rate prediction.
    Input is .npy file location in string format.
    """

    # Initialize list of dataset files' name
    temp_input = []

    # Input list of dataset files' name
    # I. Gene + miRNA
    if (dataset==7) or (dataset==8) or (dataset==9):
        n_dataset = 2
        # 1. Gene Expression
        if (dataset==7):    # 1.a. Gene htsec-count
            temp_input.append(INPUT_GEN_GEN_MIR_SURVIVAL_COUNT)
        elif (dataset==8):  # 1.b. Gene htsec-FPKM
            temp_input.append(INPUT_GEN_GEN_MIR_SURVIVAL_FPKM)
        elif (dataset==9):  # 1.c. Gene htsec-FPKMUQ
            temp_input.append(INPUT_GEN_GEN_MIR_SURVIVAL_FPKMUQ)
        # 2. miRNA Expression
        temp_input.append(INPUT_MIR_GEN_MIR_SURVIVAL)
        # Labels
        temp_label = LABELS_GEN_MIR_SURVIVAL
    
    # II. Methylation + Gene + miRNA
    elif (dataset==10) or (dataset==12) or (dataset==14):
        n_dataset = 3
        # 1. Methylation Platform GPL8490  (27578 cpg sites)
        temp_input.append(INPUT_MET_MET_GEN_MIR_SURVIVAL)
        # 2. Gene Expression
        if (dataset==10):    # 2.a. Gene htsec-count
            temp_input.append(INPUT_GEN_MET_GEN_MIR_SURVIVAL_COUNT)
        elif (dataset==12):  # 2.b. Gene htsec-FPKM
            temp_input.append(INPUT_GEN_MET_GEN_MIR_SURVIVAL_FPKM)
        elif (dataset==14):  # 2.c. Gene htsec-FPKMUQ
            temp_input.append(INPUT_GEN_MET_GEN_MIR_SURVIVAL_FPKMUQ)
        # 3. miRNA Expression
        temp_input.append(INPUT_MIR_MET_GEN_MIR_SURVIVAL)
        # Labels
        temp_label = LABELS_MET_GEN_MIR_SURVIVAL
    
    # III. Methylation (Long) + Gene + miRNA
    elif (dataset==11) or (dataset==13) or (dataset==15):
        n_dataset = 3
        # 1. Methylation Platform GPL16304 (485577 cpg sites)
        temp_input.append(INPUT_METLONG_METLONG_GEN_MIR_SURVIVAL)
        # 2. Gene Expression
        if (dataset==11):    # 2.a. Gene htsec-count
            temp_input.append(INPUT_GEN_METLONG_GEN_MIR_SURVIVAL_COUNT)
        elif (dataset==13):  # 2.b. Gene htsec-FPKM
            temp_input.append(INPUT_GEN_METLONG_GEN_MIR_SURVIVAL_FPKM)
        elif (dataset==15):  # 2.c. Gene htsec-FPKMUQ
            temp_input.append(INPUT_GEN_METLONG_GEN_MIR_SURVIVAL_FPKMUQ)
        # 3. miRNA Expression
        temp_input.append(INPUT_MIR_METLONG_GEN_MIR_SURVIVAL)
        # Labels
        temp_label = LABELS_METLONG_GEN_MIR_SURVIVAL

    
    min_max_scaler = MinMaxScaler()     # Initialize normalization function
    rval = []                           # Initialize list of outputs

    # Iterate for the number of dataset
    for j in range(n_dataset):
        # Load the dataset as 'numpy.ndarray'
        try:
            input_set = numpy.load(temp_input[j])
            label_set = numpy.load(temp_label)
        except Exception as e:
            sys.exit("Change your choice of features because the data is not available")

        # feature selection by PCA
        if pca == 1:
            pca0 = PCA(n_components=600)
            input_set = pca0.fit_transform(input_set)

        # normalize input
        input_set = min_max_scaler.fit_transform(input_set)

        rval.extend((input_set, label_set))

    return rval


def mDBN(_X_0, _X_1, _X_2 , _weights, _biases, dropout_keep_prob, activation_function):
    if activation_function == 1:
        fc = tf.nn.sigmoid
    elif activation_function == 2:
        fc = tf.nn.relu
    elif activation_function == 3:
        fc = tf.nn.tanh

    if len(_weights) == 3:
        W_1, W_2, W_3 = _weights
        b_1, b_2, b_3 = _biases
    elif len(_weights) == 4:
        W_0, W_1, W_2, W_3 = _weights
        b_0, b_1, b_2, b_3 = _biases
        temp_X_0 = tf.nn.dropout(fc(tf.add(tf.matmul(_X_0, W_0[0]), b_0[0])), dropout_keep_prob)
        for i in range(len(W_0)-1):
            temp_X_0 = tf.nn.dropout(fc(tf.add(tf.matmul(temp_X_0, W_0[i+1]), b_0[i+1])), dropout_keep_prob)
    
    temp_X_1 = tf.nn.dropout(fc(tf.add(tf.matmul(_X_1, W_1[0]), b_1[0])), dropout_keep_prob)
    for i in range(len(W_1)-1):
        temp_X_1 = tf.nn.dropout(fc(tf.add(tf.matmul(temp_X_1, W_1[i+1]), b_1[i+1])), dropout_keep_prob)

    temp_X_2 = tf.nn.dropout(fc(tf.add(tf.matmul(_X_2, W_2[0]), b_2[0])), dropout_keep_prob)
    for i in range(len(W_2)-1):
        temp_X_2 = tf.nn.dropout(fc(tf.add(tf.matmul(temp_X_2, W_2[i+1]), b_2[i+1])), dropout_keep_prob)

    if len(_weights) == 3:
        temp_X = tf.concat((temp_X_1,temp_X_2),axis=1)
    elif len(_weights) == 4:
        temp_X = tf.concat((tf.concat((temp_X_0,temp_X_1),axis=1),temp_X_2), axis=1)

    out = tf.nn.dropout(fc(tf.add(tf.matmul(temp_X, W_3[0]), b_3[0])), dropout_keep_prob)
    for i in range(len(W_3)-2):
        out = tf.nn.dropout(fc(tf.add(tf.matmul(out, W_3[i+1]), b_3[i+1])), dropout_keep_prob)
    out = tf.add(tf.matmul(out, W_3[-1]), b_3[-1])
    
    return (tf.transpose(out))[0]


def test_mDBN(finetune_lr=0.1,
    pretraining_epochs=100,
    pretrain_lr=0.01,
    training_epochs=100,
    dataset=6, batch_size=10,
    layers_met=[1000, 1000, 1000],
    layers_gen=[1000, 1000, 1000],
    layers_mir=[1000, 1000, 1000],
    layers_tot=[500, 500, 500],
    dropout=0.2,
    pca=2,
    optimizer=1,
    activation_function=1):
	
    # Title
    print("\nSurvival Rate Regression with ", end="")
    if (dataset==10) or (dataset==12) or (dataset==14):
        print("DNA Methylation Platform GPL8490, ", end="")
    if (dataset==11) or (dataset==13) or (dataset==15):
        print("DNA Methylation Platform GPL16304, ", end="")
    if (dataset==7) or (dataset==10) or (dataset==11):
        print("Gene Expression HTSeq Count, ", end="")
    if (dataset==8) or (dataset==12) or (dataset==13):
        print("Gene Expression HTSeq FPKM, ", end="")
    if (dataset==9) or (dataset==14) or (dataset==15):
        print("Gene Expression HTSeq FPKM-UQ, ", end="")
    print("miRNA Expression (Theano)\n")

    # Dataset amount
    if (dataset>=7) and (dataset<=9):       # Gene + miRNA
        n_dataset = 2
    elif (dataset>=10) and (dataset<=15):   # Methylation + Gene + miRNA
        n_dataset = 3
    
    # Loading dataset
    datasets = load_data(dataset, pca)

    #############################################################################
    ################################# DBN LVL-1 #################################
    #############################################################################
    # List of parameters
    Ws_0 = []   # params for low-lvl DBN DNA Methylation part
    bs_0 = []
    Ws_1 = []   # params for low-lvl DBN Gene Expression part
    bs_1 = []
    Ws_2 = []   # params for low-lvl DBN miRNA Expression part
    bs_2 = []

    # Iterate for number of datasets
    for nr_dataset in range(n_dataset):
        # Title and dataset type
        if n_dataset == 2:
            if nr_dataset == 0:
                dataset_type = 1
                print("\nDBN lvl 1: Gene Expression data\n")
            elif nr_dataset == 1:
                dataset_type = 2
                print("\nDBN lvl 1: miRNA Expression data\n")
        if n_dataset == 3:
            if nr_dataset == 0:
                dataset_type = 0
                print("\nDBN lvl 1: DNA Methylation data\n")
            elif nr_dataset == 1:
                dataset_type = 1
                print("\nDBN lvl 1: Gene Expression data\n")
            elif nr_dataset == 2:
                dataset_type = 2
                print("\nDBN lvl 1: miRNA Expression data\n")

        ############################## PREPARE DATASET ##############################
        # take input and label set
        if n_dataset == 2:
            input_set = datasets[nr_dataset*2]
            label_set = datasets[(nr_dataset*2)+1]
        elif n_dataset == 3:
            input_set = datasets[nr_dataset*2]
            label_set = datasets[(nr_dataset*2)+1]

        # Split dataset into training and test set
        X_train, X_test, Y_train, Y_test = train_test_split(input_set, label_set, test_size=0.25, random_state=100)


        ############################### BUILD NN MODEL ##############################
        print('Build NN Model')
            
        if dataset_type == 0:
            dbn = UnsupervisedDBN(hidden_layers_structure=layers_met,
                                  activation_function='relu',
                                  optimization_algorithm='sgd',
                                  learning_rate_rbm=pretrain_lr,
                                  n_epochs_rbm=pretraining_epochs,
                                  batch_size=batch_size)
        elif dataset_type == 1:
            dbn = UnsupervisedDBN(hidden_layers_structure=layers_gen,
                                  activation_function='relu',
                                  optimization_algorithm='sgd',
                                  learning_rate_rbm=pretrain_lr,
                                  n_epochs_rbm=pretraining_epochs,
                                  batch_size=batch_size)
        elif dataset_type == 2:
            dbn = UnsupervisedDBN(hidden_layers_structure=layers_mir,
                                  activation_function='relu',
                                  optimization_algorithm='sgd',
                                  learning_rate_rbm=pretrain_lr,
                                  n_epochs_rbm=pretraining_epochs,
                                  batch_size=batch_size)


        ############################# PRETRAIN NN MODEL #############################
        print('Pretrain NN Model')

        dbn.fit(X_train)

        
        ########################### SAVE DBN LVL-1 RESULTS ###########################
        # save Ws,bs from [W,b,W,b,...,W,b] of dbn.params
        if dataset_type == 0:
            for idx_param in range(len(layers_met)):
                Ws_0.extend([sess.run(dbn.rbm_layers[idx_param].W)])
                bs_0.extend([sess.run(dbn.rbm_layers[idx_param].c)])
        elif dataset_type == 1:
            for idx_param in range(len(layers_gen)):
                Ws_1.extend([sess.run(dbn.rbm_layers[idx_param].W)])
                bs_1.extend([sess.run(dbn.rbm_layers[idx_param].c)])
        elif dataset_type == 2:
            for idx_param in range(len(layers_mir)):
                Ws_2.extend([sess.run(dbn.rbm_layers[idx_param].W)])
                bs_2.extend([sess.run(dbn.rbm_layers[idx_param].c)])

        # save output (last layer output of DBN lvl-1)
        if dataset_type == 0:
            dbn_lvl1_out_0 = dbn.transform(X_train)
        elif dataset_type == 1:
            dbn_lvl1_out_1 = dbn.transform(X_train)
        elif dataset_type == 2:
            dbn_lvl1_out_2 = dbn.transform(X_train)
    
    
    
    #############################################################################
    ################################# DBN LVL-2 #################################
    #############################################################################
    # Title for DBN lvl-2
    print("\nDBN lvl 2\n")


    ############################## PREPARE DATASET ##############################
    # Concatenate output of DBN lvl-1 as input for DBN lvl-2
    if n_dataset == 2:
        X_train = np.concatenate((dbn_lvl1_out_1,dbn_lvl1_out_2),axis=1)
    elif n_dataset == 3:
        X_train = np.concatenate((np.concatenate((dbn_lvl1_out_0,dbn_lvl1_out_1),axis=1),dbn_lvl1_out_2), axis=1)


    ############################### BUILD NN MODEL ##############################
    print('Build NN Model')
    dbn = UnsupervisedDBN(hidden_layers_structure=layers_tot,
                          activation_function='relu',
                          optimization_algorithm='sgd',
                          learning_rate_rbm=pretrain_lr,
                          n_epochs_rbm=pretraining_epochs,
                          batch_size=batch_size)


    ############################# PRETRAIN NN MODEL #############################
    print('Pretrain NN Model')
    
    dbn.fit(X_train)


    ########################### SAVE DBN LVL-2 RESULTS ##########################
    Ws_3 = []   # params for lvl-2 DBN
    bs_3 = []

    for idx_param in range(len(layers_tot)):
        Ws_3.extend([sess.run(dbn.rbm_layers[idx_param].W)])
        bs_3.extend([sess.run(dbn.rbm_layers[idx_param].c)])


    
    #############################################################################
    #################################### MDBN ###################################
    #############################################################################
    # Title for mDBN
    print("\nmDBN\n")


    ############################## PREPARE DATASET ##############################
    # 1. input + output
    Xs_train = []
    Xs_test = []

    for nr_dataset in range(n_dataset):
        # take input and label set
        if n_dataset == 2:
            input_set = datasets[nr_dataset*2]
            label_set = datasets[(nr_dataset*2)+1]
            # placeholder
            if nr_dataset == 0:
                X_1 = tf.placeholder(tf.float32, [None, input_set.shape[1]])
            elif nr_dataset == 1:
                X_2 = tf.placeholder(tf.float32, [None, input_set.shape[1]])
        elif n_dataset == 3:
            input_set = datasets[nr_dataset*2]
            label_set = datasets[(nr_dataset*2)+1]
            # placeholder
            if nr_dataset == 0:
                X_0 = tf.placeholder(tf.float32, [None, input_set.shape[1]])
            elif nr_dataset == 1:
                X_1 = tf.placeholder(tf.float32, [None, input_set.shape[1]])
            elif nr_dataset == 2:
                X_2 = tf.placeholder(tf.float32, [None, input_set.shape[1]])

        # Split dataset into training and test set
        X_train, X_test, Y_train, Y_test = train_test_split(input_set, label_set, test_size=0.25, random_state=100)

        # save in list
        Xs_train.append(X_train)
        Xs_test.append(X_test)

    # 2. weights + biases
    W_1 = [tf.Variable(np.transpose(Ws_1[i])) for i in range(len(Ws_1))]
    b_1 = [tf.Variable(np.transpose(bs_1[i])) for i in range(len(bs_1))]
    W_2 = [tf.Variable(np.transpose(Ws_2[i])) for i in range(len(Ws_2))]
    b_2 = [tf.Variable(np.transpose(bs_2[i])) for i in range(len(bs_2))]
    W_3 = [tf.Variable(np.transpose(Ws_3[i])) for i in range(len(Ws_3))]
    b_3 = [tf.Variable(np.transpose(bs_3[i])) for i in range(len(bs_3))]
    W_3.append(tf.Variable(tf.random_normal([layers_tot[-1], 1],stddev=0.1)))
    b_3.append(tf.Variable(tf.random_normal([1])))

    if n_dataset == 2:
        weights = [W_1,W_2,W_3]
        biases = [b_1,b_2,b_3]
    elif n_dataset == 3:
        W_0 = [tf.Variable(np.transpose(Ws_0[i])) for i in range(len(Ws_0))]
        b_0 = [tf.Variable(np.transpose(bs_0[i])) for i in range(len(bs_0))]
        weights = [W_0,W_1,W_2,W_3]
        biases = [b_0,b_1,b_2,b_3]

    # 3. TensorFlow output and dropout placeholders
    y = tf.placeholder(tf.float32, [None, ])
    dropout_keep_prob = tf.placeholder(tf.float32)


    ############################### BUILD NN MODEL ##############################
    print('Build NN Model')
    if n_dataset == 2:
        logits = mDBN(_X_0=X_1, _X_1=X_1, _X_2=X_2, _weights=weights, _biases=biases, dropout_keep_prob=dropout_keep_prob, activation_function=activation_function)
    elif n_dataset == 3:
        logits = mDBN(_X_0=X_0, _X_1=X_1, _X_2=X_2, _weights=weights, _biases=biases, dropout_keep_prob=dropout_keep_prob, activation_function=activation_function)

    # Loss and Optimizer
    J = tf.reduce_mean(tf.square(logits - y))
    if optimizer == 1:
        optimizer = tf.train.GradientDescentOptimizer(learning_rate=finetune_lr)
    elif optimizer == 2:
        optimizer = tf.train.RMSPropOptimizer(learning_rate=finetune_lr)
    elif optimizer == 3:
        optimizer = tf.train.AdamOptimizer(learning_rate=finetune_lr)
    train = optimizer.minimize(J)

    # Initializing the variables
    sess.run(tf.global_variables_initializer())

    
    ############################# FINETUNE NN MODEL #############################
    print('Train NN Model')

    for epoch in range(training_epochs):
        avg_cost = 0.
        total_batch = int(Xs_train[0].shape[0] / batch_size)
        
        for i in range(total_batch):
            if n_dataset == 2:
                batch_xs_1 = Xs_train[0][(i*batch_size):((i+1)*batch_size)]
                batch_xs_2 = Xs_train[1][(i*batch_size):((i+1)*batch_size)]
            elif n_dataset == 3:
                batch_xs_0 = Xs_train[0][(i*batch_size):((i+1)*batch_size)]
                batch_xs_1 = Xs_train[1][(i*batch_size):((i+1)*batch_size)]
                batch_xs_2 = Xs_train[2][(i*batch_size):((i+1)*batch_size)]
            batch_ys = Y_train[(i*batch_size):((i+1)*batch_size)]
                
            if n_dataset == 2:
                _, c = sess.run([train, J], feed_dict={X_1: batch_xs_1, X_2: batch_xs_2, y: batch_ys, dropout_keep_prob: 1.-dropout})
            elif n_dataset == 3:
                _, c = sess.run([train, J], feed_dict={X_0: batch_xs_0, X_1: batch_xs_1, X_2: batch_xs_2, y: batch_ys, dropout_keep_prob: 1.-dropout})
            
            avg_cost += c / total_batch
        
        if epoch % 10 == 0:
            print("Epoch:", '%04d' % (epoch+1), "cost={:.9f}".format(avg_cost))

    
    
    ############################### TEST NN MODEL ###############################
    print('Test NN Model')

    if n_dataset == 2:
        Y_pred = sess.run(logits, feed_dict={X_1: Xs_test[0], X_2: Xs_test[1], dropout_keep_prob: 1.})
        Y_pred_train = sess.run(logits, feed_dict={X_1: Xs_train[0], X_2: Xs_train[1], dropout_keep_prob: 1.})
    elif n_dataset == 3:
        Y_pred = sess.run(logits, feed_dict={X_0: Xs_test[0], X_1: Xs_test[1], X_2: Xs_test[2], dropout_keep_prob: 1.})
        Y_pred_train = sess.run(logits, feed_dict={X_0: Xs_train[0], X_1: Xs_train[1], X_2: Xs_train[2], dropout_keep_prob: 1.})

    # msa and r2
    mse = mean_squared_error(Y_test, Y_pred)
    r2 = r2_score(Y_test, Y_pred)
    tmse = mean_squared_error(Y_train, Y_pred_train)
    tr2 = r2_score(Y_train, Y_pred_train)

    # print results
    print("MSE = " + str(mse))
    print("R2 = " + str(r2))
    print("tMSE = " + str(tmse))
    print("tR2 = " + str(tr2))


if __name__ == '__main__':
    start = timeit.default_timer()

    print("\n\nWhat type of features do you want to use?")
    print("[1] DNA Methylation")
    print("[2] Gene Expression")
    print("[3] miRNA Expression")
    
    try:
        features = input("Insert here [default = 3]: ")
    except Exception as e:
        features = 3

    if features == 1:   # if DNA Methylation is picked
        print("You will use DNA Methylation data to create the prediction")
        print("\nWhat type DNA Methylation data do you want to use?")
        print("[1] Platform GPL8490\t(27578 cpg sites)")
        print("[2] Platform GPL16304\t(485577 cpg sites)")
        try:
            met = input("Insert here [default = 1]: ")
        except Exception as e:
            met = 1
        
        if met == 2: # if Platform GPL16304 is picked
            print("You will use DNA Methylation Platform GPL16304 data")
            DATASET = 2
        else:       # if Platform GPL8490 or any other number is picked
            print("You will use DNA Methylation Platform GPL8490 data")
            DATASET = 1
        
    elif features == 2: # if Gene Expression is picked
        print("You will use Gene Expression data to create the prediction")
        print("\nWhat type Gene Expression data do you want to use?")
        print("[1] Count")
        print("[2] FPKM")
        print("[3] FPKM-UQ")
        try:
            gen = input("Insert here [default = 1]: ")
        except Exception as e:
            gen = 1
        
        if gen == 2:    # if FPKM is picked
            print("You will use Gene Expression FPKM data")
            DATASET = 4
        elif gen == 3:  # if FPKM-UQ is picked
            print("You will use Gene Expression FPKM-UQ data")
            DATASET = 5
        else:           # if Count or any other number is picked
            print("You will use Gene Expression Count data")
            DATASET = 3
        
    else:   # if miRNA Expression or any other number is picked
        DATASET = 6
        print("You will use miRNA Expression data to create the prediction")

    test_mDBN(dataset=DATASET)

    stop = timeit.default_timer()
    print(stop-start)