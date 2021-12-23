##################################
############### Requirement----- tensroflow version 2.3.0...--------##########################
###################################

from _datetime import date, datetime
import json
#import xlsxwriter
import os
import numpy as np
import pandas as pd
import tensorflow as tf
from keras.models import load_model, Sequential
from sklearn.preprocessing import StandardScaler
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from Bio import SeqIO
from Bio.SeqUtils.ProtParam import ProteinAnalysis
import csv


# Paths to folders
upload_filepath_csv= os.path.join('custom_directory','uploaded_files','csv_files')
upload_filepath_fasta= os.path.join('custom_directory','uploaded_files','fasta_files')
model_filepath = os.path.join('custom_directory','saved_models')
model_results = os.path.join('custom_directory','results')

# extension allowed
ALLOWED_EXTENSIONS = {'fasta'}

# Flask App
app = Flask(__name__)

app.config['upload_filepath_csv'] = upload_filepath_csv
app.config['upload_filepath_fasta'] = upload_filepath_fasta
app.config['model_filepath'] = model_filepath
app.config['model_results'] = model_results

# functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# activation functions
def sielu(x):
    return 0.5 * x * (2 * tf.sigmoid(2 * tf.sqrt(2 / np.pi) * (x + 0.044715 * tf.pow(x, 3))))
    #return 0.5 * x * (1 + tf.sigmoid(tf.sqrt(2 / np.pi) * (x + 0.044715 * tf.pow(x, 3))))

def gelu(x):
    return 0.5 * x * (1 + tf.tanh(tf.sqrt(2 / np.pi) * (x + 0.044715 * tf.pow(x, 3))))

# Dataset Prepocessing
def data_preprocess(f):
    filename = f
    data = pd.read_csv(os.path.join(app.config['upload_filepath_csv'], filename))
    # corr = data.corr()
    # columns = np.full((corr.shape[0],), True, dtype=bool)
    # for i in range(corr.shape[0]):
    #     for j in range(i + 1, corr.shape[0]):
    #         if corr.iloc[i, j] >= 0.8:
    #             if columns[j]:
    #                 columns[j] = False
    # selected_columns = data.columns[columns]
    # data_predict = data[selected_columns]
    seq_id = data.iloc[:, 0].values
    x = data.iloc[:, 1:].values  # all rows and 2nd to all remaining coloumn

    preprocess = StandardScaler()
    x = preprocess.fit_transform(x)
    x = np.reshape(x,(x.shape[0], x.shape[1], 1))
    return x, seq_id

#### function that extract features from fasta file to a csv file
def fastaToCSV(f):
    fasta_file=f
    f, e = os.path.splitext(fasta_file)
    fasta_file_path=os.path.join(app.config['upload_filepath_fasta'], fasta_file)
    complete_feature_List = []
    for record in SeqIO.parse(fasta_file_path, "fasta"):
        feature_row_list = []

        ##### Amino Acids
        seqid = str(record.id)
        feature_row_list.append(seqid)
        seq = str(record.seq)
        X = ProteinAnalysis(seq)
        aaDict = X.count_amino_acids()
        for aa in aaDict:
            feature_row_list.append(aaDict.get(aa, 0))

        # percentage
        PDict = X.get_amino_acids_percent()
        for aa in PDict:
            feature_row_list.append(PDict.get(aa, 0))

        # Molecular Weight
        W = X.molecular_weight()
        feature_row_list.append(W)

        # Aromaticity
        A = X.aromaticity()
        feature_row_list.append(A)

        # Instability
        I = X.instability_index()
        feature_row_list.append(I)

        # GRAVY
        G = X.gravy()
        feature_row_list.append(G)

        # ISO-Electric point
        PI = X.isoelectric_point()
        feature_row_list.append(PI)

        # secondary
        SS = X.secondary_structure_fraction()
        feature_row_list.append(SS[0])
        feature_row_list.append(SS[1])
        feature_row_list.append(SS[2])

        complete_feature_List.append(feature_row_list)
    csv_file = f+'.csv'
    with open(os.path.join(app.config['upload_filepath_csv'], csv_file), 'w') as f11:
        writer = csv.writer(f11)
        writer.writerows(complete_feature_List)
    return csv_file


# Home page
@app.route('/',methods = ['POST', 'GET'])
def home_screen():
    return render_template('test.html')

# Dataset upload
@app.route('/upload',methods = ['POST', 'GET'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'dataset_file' not in request.files:
            # flash('No file part')
            return json.dumps({
                'status':'NOT OK'
                               })
        file = request.files['dataset_file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            return json.dumps({
                'status':'NOT OK'
                               })
        if(allowed_file(file.filename)):
            if file:
                filename = secure_filename(file.filename)
                f, e = os.path.splitext(filename)
                today = datetime.now()
                today = today.strftime("%d_%m_%y_%H_%M_%S")
                newFileNme = f + '_' + today + e
                file.save(os.path.join(app.config['upload_filepath_fasta'], newFileNme))
                new_csv_file = fastaToCSV(newFileNme)
                return json.dumps({
                    'status':'OK',
                    'file_name':new_csv_file
                                   })
            else:
                return json.dumps({
                    'status': 'NOT OK'
                })
        else:
            return json.dumps({
                'status': 'NOT CSV'
            })
    else:
        return json.dumps({
            'status': 'NOT OK'
        })

# Prediction with the saved models
@app.route('/model',methods = ['POST', 'GET'])
def loading_model():
    filename = None
    modeltype= None
    activationtype = None
    act=None
    mod=None
    if request.method == 'POST':
        if 'file_name' not in request.form:
            return json.dumps({
                'status':'File not uploaded'
                               })
        filename = request.form['file_name']
        if filename =='':
            return json.dumps({
                'status': 'NO FILE'
            })
        modeltype = request.form['model_type']
        activationtype = request.form['act_type']

        f, e = os.path.splitext(filename)

        if(modeltype=='Drought'):
            mod='drought'
            if (activationtype == 'Sielu'):
                act = 'sielu'
            if (activationtype == 'Gelu'):
                    act = 'gelu'
        elif(modeltype=='Heat'):
            mod ='heat'
            if (activationtype == 'Sielu'):
                act = 'sielu'
            if (activationtype == 'Gelu'):
                act = 'gelu'
        elif(modeltype=='Cold'):
            mod='cold'
            if (activationtype == 'Sielu'):
                act = 'sielu'
            if (activationtype == 'Gelu'):
                act = 'gelu'
        elif(modeltype=='Salt'):
            mod='salt'
            if (activationtype == 'Sielu'):
                act = 'sielu'
            if (activationtype == 'Gelu'):
                act = 'gelu'

        model_file ='model_'+mod+'_'+act+'.h5'
        x, y = data_preprocess(filename)
        my_model = Sequential()
        if(activationtype == 'Gelu'):
            my_model = load_model(os.path.join(app.config['model_filepath'], model_file),
                              custom_objects={'gelu': gelu})
        if (activationtype == 'Sielu'):
            my_model = load_model(os.path.join(app.config['model_filepath'], model_file),
                                  custom_objects={'sielu': sielu})
        my_model.summary()
        y_pred = my_model.predict_classes(x)
        y_df = pd.DataFrame(y_pred)
        result_file=f+'_'+ mod+'_'+act+'_results.xlsx'
        writer= pd.ExcelWriter(os.path.join(app.config['model_results'], result_file),
                               engine='xlsxwriter')
        y_df.to_excel(writer, header=True, sheet_name='predicted Values')
        writer.save()
        return json.dumps({'status': 'OK',
                           'result_filename':result_file,
                           'result_file_path': app.config['model_results']
                           });
    else:
        return json.dumps({
            'status': 'NOT OK'
        })

# File download
@app.route('/download/<file>',methods = ['GET'])
def download(file):
    path = os.getcwd()
    path_rs=path+"/"+app.config['model_results']+ "/"+file
    return send_file(path_rs,
                    mimetype='text/csv',
                    attachment_filename=file,
                    as_attachment=True)

# run the api
if __name__ == '__main__':
   app.run(host= "0.0.0.0", debug=False, threaded= False)