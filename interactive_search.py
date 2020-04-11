import numpy as np
from sentence_transformers import SentenceTransformer
import scipy
import pandas as pd
import os
import textwrap
import json
import prettytable
import logging
import pickle
import warnings
warnings.simplefilter('ignore')

METADATA_PATH = 'data/metadata_codevscovid.csv'

DATA_PATH = 'data'
MODELS_PATH = 'models'
MODEL_NAME = 'scibert-nli'
CORPUS_PATH = os.path.join(DATA_PATH, 'corpus.pkl')
MODEL_PATH = os.path.join(MODELS_PATH, MODEL_NAME)
EMBEDDINGS_PATH = os.path.join(DATA_PATH, f'{MODEL_NAME}-embeddings.pkl')
# EMBEDDINGS_NP_PATH = os.path.join(DATA_PATH, f'{MODEL_NAME}-embeddings.npy')


# corpus dimesions :
# 0: abstract
# 1: date
# 2: language
def cache_corpus(mode='CSV'):
    corpus = []
    if mode == 'CSV':
        df = pd.read_csv(METADATA_PATH)
        test = df[['abstract',
                   'publish_time',
                   'language',
                   'title',
                   'url',
                   'main_topic',
                   'main_subtopic',
                   'cord_uid']]
        for a, b, c, d, e, f, g, h in test.itertuples(index=False):
            if type(a) == str and a != "Unknown":
                corpus.append([a, b, c, d, e, f, g, h])
        print('Corpus size', len(corpus))
    elif mode == 'JSON':
        raise NotImplementedError('Feature removed')
    else:
        raise AttributeError('Mode should be either CSV or JSON')
    with open(CORPUS_PATH, 'wb') as file:
        pickle.dump(corpus, file)
    return corpus

# return true if search filters are satisified


def check_constraints(filters, date, lang):
    valid = True
    [date_filter_min, date_filter_max, language_filter] = filters
    date = int(date[:4])
    if date_filter_min is not None:
        if date < date_filter_min:
            valid = False
    if date_filter_max is not None:
        if date > date_filter_max:
            valid = False
    if language_filter is not None:
        if lang != language_filter:
            valid = False

    return valid


def ask_question(query, model, corpus, corpus_embed, filters, top_k=5):
    """
    Adapted from https://www.kaggle.com/dattaraj/risks-of-covid-19-ai-driven-q-a
    """
    queries = [query]
    query_embeds = model.encode(queries, show_progress_bar=False)
    for query, query_embed in zip(queries, query_embeds):
        distances = scipy.spatial.distance.cdist(
            [query_embed], corpus_embed, "cosine")[0]
        distances = zip(range(len(distances)), distances)
        distances = sorted(distances, key=lambda x: x[1])
        results = []
        j = 0
        for count, (idx, distance) in enumerate(distances):
            # TODO check the filters
            date = corpus[idx][1]
            lang = corpus[idx][2]
            title = corpus[idx][3]
            url = corpus[idx][4]
            theme = corpus[idx][5]
            sub_theme = corpus[idx][6]
            cord_uid = corpus[idx][7]

            if check_constraints(filters, date, lang):
                j += 1
                results.append([count + 1, corpus[idx][0].strip(), round(1 - distance, 4),
                                date, lang, title, url, theme, sub_theme, cord_uid])
            if j >= top_k:
                break
    return results


def show_answers(results):
    table = prettytable.PrettyTable(
        ['Rank', 'Abstract', 'Score', 'Date', 'Language']
    )
    for res in results:
        rank = res[0]
        text = res[1]
        text = textwrap.fill(text, width=75)
        text = text + '\n\n'
        score = res[2]
        date = res[3]
        language = res[4]
        table.add_row([
            rank,
            text,
            score,
            date,
            language
        ])
    print('\n')
    print(str(table))
    print('\n')


# save the answers into a json
def save_answers(results):
    dict_result = {}
    for i in range(len(results)):
        rank = results[i][0]
        abstract = results[i][1]
        score = results[i][2]
        date = results[i][3]
        language = results[i][4]

        dict_result[str(rank)] = []
        dict_result[str(rank)] = {
            'abstract': abstract,
            'score': score,
            'date': date,
            'language': language
        }

    with open('results.json', 'w') as outfile:
        json.dump(dict_result, outfile, ensure_ascii=False, indent=4)
    # check dates selected by user are valid


def verify_date(date_str, earliest=None):
    verification = True

    if date_str:
        date_int = float(date_str)

        if not date_int.is_integer():
            print('The date is not an integer. Please re-enter')
            verification = False
        if date_int > 2020:
            print('date can not be bigger than 2020. Please re-enter')
            verification = False
        if date_int < 1951:
            print('date can not be smaller than 1951. Please re-enter')
            verification = False
        if earliest is not None:
            if date_int < earliest:
                print('This date must be bigger than',
                      earliest, '. Please re-enter')
                verification = False
    else:
        date_int = None
        print('No date selected')

    return verification, date_int


# check languages selected by user are valid
def verify_language(language):
    verification = True

    if language:
        if language not in ['de', 'en', 'es', 'fr', 'it', 'ja', 'pt', 'zh']:
            print('language not valid. Please re-enter')
            verification = False
    else:
        language = None

    return verification, language


if __name__ == '__main__':
    os.system('cls' if os.name == 'nt' else 'clear')
    if not os.path.exists(CORPUS_PATH):
        print("Caching the corpus for future use...")
        corpus = cache_corpus()
    else:
        print("Loading the corpus from", CORPUS_PATH, '...')
        with open(CORPUS_PATH, 'rb') as corpus_pt:
            corpus = pickle.load(corpus_pt)

    corpus_abstract = []
    model = SentenceTransformer(MODEL_PATH)
    for i in range(len(corpus)):
        corpus_abstract.append(corpus[i][0])

    if not os.path.exists(EMBEDDINGS_PATH):
        print("Computing and caching model embeddings for future use...")
        embeddings = model.encode(corpus_abstract, show_progress_bar=True)
        with open(EMBEDDINGS_PATH, 'wb') as file:
            pickle.dump(embeddings, file)
    else:
        print("Loading model embeddings from", EMBEDDINGS_PATH, '...')
        with open(EMBEDDINGS_PATH, 'rb') as file:
            embeddings = pickle.load(file)

    while True:
        verified = False
        query = input('\nAsk your question: ')

        while not verified:
            date_filter_min = input('\nEarliest year (i.e. 2016 or None): ')
            verified, date_filter_min = verify_date(date_filter_min)

        verified = False
        while not verified:
            date_filter_max = input('\nLatest year (i.e. 2020 or None): ')
            verified, date_filter_max = verify_date(
                date_filter_max, date_filter_min)

        verified = False
        while not verified:
            language_filter = input(
                '\nLanguage (i.e. de, en, es, fr, it, ja, pt, zh or None): ')
            verified, language_filter = verify_language(language_filter)

        filters = [date_filter_min, date_filter_max, language_filter]
        results = ask_question(query, model, corpus, embeddings, filters)

        # save_answers(results)
        show_answers(results)
