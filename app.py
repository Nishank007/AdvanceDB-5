from operator import and_
from os import abort
from flask import Flask, render_template, request, redirect
from flask.helpers import flash, url_for
from sqlalchemy.sql.operators import op
from sqlalchemy import func, distinct, select
from werkzeug.utils import secure_filename
from models import FilterModel, db
import urllib.parse
import csv
import copy
import os
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
import time
import re
import nltk
from nltk.stem import PorterStemmer
from nltk.stem import WordNetLemmatizer




table_creation_time = '0.82 seconds'

app = Flask(__name__)  # define app
port = int(os.getenv("PORT", 8000))

app.secret_key = 'super secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'  # sqlite file
# disable sqlalchemy event system
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads/'  # path to upload folder
db.init_app(app)  # initialize app


with open('stopwords.txt')as f:
    stopwords_string=f.read()
stopwords_list = stopwords_string.replace('"', '').split()



stm = PorterStemmer()
lmtz = WordNetLemmatizer()



def freq(str):
  
    # break the string into list of words 
    str = str.split()         
    str2 = []
    freq_list = []
    # loop till string values present in list str
    for i in str:             
  
        # checking for the duplicacy
        if i not in str2:
  
            # insert value in str2
            str2.append(i) 
              
    for i in range(0, len(str2)):
  
        # count the frequency of each word(present 
        # in str2) in str and print
        # print('Frequency of', str2[i], 'is :', str.count(str2[i])) 
        freq_list.append({'word':str2[i],'freq':str.count(str2[i])})
    return freq_list


def lower(text):
    return text.lower()


def remove_punctuation(text):
    text = re.sub(r'[^\w\s]+', ' ', text)
    return text


def remove_stopwords(text):
    text = ' '.join([word for word in text.split() if word not in stopwords_list])
    return text


def stem_text(text):
    text = ' '.join([stm.stem(word) for word in text.split()])
    return text

def ngrams(input, n):
    input = input.split(' ')
    output = []
    for i in range(len(input)-n+1):
        output.append(input[i:i+n])
    return output



# executed before first request
@app.before_first_request
def create_table():
    db.create_all()  # create all tables


# base url
@app.route('/')
def home():
    file_list = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('index.html',file_list=file_list)

# SQL random query


@app.route('/results/random', methods=['GET', 'POST'])
def results_1():
    if request.method == 'POST':
        name = request.form['name']
        text = request.form['text']
        lowercase_text = lower(text)
        no_punc_text = remove_punctuation(lowercase_text)
        word_list = no_punc_text.split()

        with open(os.path.join(app.config['UPLOAD_FOLDER'],name+'.txt'),'w+') as f:
            f.write(no_punc_text)

        freq_list = freq(no_punc_text)
    return render_template('data.html',name=name+'.txt',word_list=word_list, word_count=len(word_list), text=no_punc_text,freq_list=freq_list)


# SQL restricted query
@app.route('/results/random2', methods=['GET', 'POST'])
def results_2():
    if request.method == 'POST':
        search = request.form['search']
        name = request.form['name']
        count=0
        if search != '':
            with open(os.path.join(app.config['UPLOAD_FOLDER'],name),'r') as f:
                text = f.read()
                word_list = text.split()
                for obj in word_list:
                    if obj == search:
                        count+=1
    return render_template('datalist.html', count=count)



@app.route('/results/random3', methods=['GET', 'POST'])
def results_3():
    if request.method == 'POST':
            display_list = []
            file_list = os.listdir(app.config['UPLOAD_FOLDER'])
            for index,file in enumerate(file_list):
                if os.path.splitext(file)[1] != '.txt':
                    # file_list.pop(index)
                    continue
                with open(os.path.join(app.config['UPLOAD_FOLDER'],file),'r') as f:
                    text = f.read()
                    text_word_list = text.split()
                    no_sw_str = remove_stopwords(text)
                    words_list = no_sw_str.split()
                    display_list.append({'name':file,'count_before':len(text_word_list),'count_after':len(words_list),'first_10_words':words_list[0:10]})
            return render_template('datalist.html', display_list=display_list)



@app.route('/results/earthquakebymag2', methods=['GET', 'POST'])
def results_4():
    if request.method == 'POST':
        name = request.form['name']
        text = request.form['text']
        display_list = []
        file_list = os.listdir(app.config['UPLOAD_FOLDER'])
        for index,file in enumerate(file_list):
            if os.path.splitext(file)[1] != '.txt':
                # file_list.pop(index)
                continue
            with open(os.path.join(app.config['UPLOAD_FOLDER'],file),'r') as f:
                text = f.read()
                text_word_list = text.split()
                no_sw_str = remove_stopwords(text)
                words_list = no_sw_str.split()
                display_list.append({'Name':file,'Count_before':len(text_word_list),'Count_after':len(words_list),'First_10_words':words_list[0:10]})
        return render_template('datalist.html', display_list=display_list)

# Your assignment is to provide a local interface (using a web page, displayed in a    browser) to a cloud service that you will implement that will allow a user to upload     earthquake data and investigate it.
# insert data into database via csv file
@app.route('/data/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.host_url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.host_url)
        if file:  # check file extension
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(
                file.filename)))  # save file to server
            with open("static/uploads/" + file.filename, newline='') as f:
                text = f.read()

                sentences = text.split('.')
                lowercase_text = lower(text)
                # stopwords_list = stopwords_string.replace('"', '').split()
                no_punc_text = remove_punctuation(lowercase_text) 
                no_sw_list = remove_stopwords(no_punc_text)
                stem_list = stem_text(no_sw_list)
                bigrams_list = ngrams(stem_list, 2)
                trigrams_list = ngrams(stem_list, 3)
                

                db.session.bulk_save_objects(filter_list)
                db.session.commit()  # write to database
            flash("Successfully added new records.")
            return render_template('index.html')


# show all records
@app.route('/data', methods=['GET', 'POST'])
def RetrieveList():
    earthquakes = FilterModel.query.filter(FilterModel.pr_id >= 1)
    return render_template('datalist.html', earthquakes=earthquakes, count=earthquakes.count())

# delete all records


@app.route('/data/delete', methods=['GET', 'POST'])
def DeleteAll():
    db.session.query(FilterModel).delete()
    db.session.commit()

    flash("Successfully deleted all records.")
    return render_template('index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port)
