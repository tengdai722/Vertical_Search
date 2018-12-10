import lda
import lda.datasets
import numpy as np
import os
from nltk.stem import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words


def lda_func(X=lda.datasets.load_reuters(),
             vocab=lda.datasets.load_reuters_vocab(),
             titles=lda.datasets.load_reuters_titles(),
             n_topics=10,
             n_top_words=8):

    # define and fit the model
    model = lda.LDA(n_topics=n_topics, n_iter=1500, random_state=1)
    model.fit(X)

    # topics
    topic_word = model.topic_word_  # model.components_ also works
    for i, topic_dist in enumerate(topic_word):
        topic_words = np.array(vocab)[np.argsort(topic_dist)][:-(n_top_words+1):-1]
        print('Topic {}: {}'.format(i, ' '.join(topic_words)))

    # document topic coverage
    doc_topic = model.doc_topic_
    for i in range(10):
        print("{} (top topic: {})".format(titles[i], doc_topic[i].argmax()))


def process():
    if not os.path.exists('processed_corpus.npz'):
        data = []
        vocab = {}
        titles = []

        # e.g. key: "Technology", value: [0, 1, 2, 3, 4]
        topic_dict = {}
        # e.g. key: "23", value: "Food"
        document_topic_str_dict = {}
        ps = PorterStemmer()
        doc_idx = 0
        idx = 0

        tokenizer = RegexpTokenizer(r'\w+')

        # create English stop words list
        en_stop = get_stop_words('en')

        for root, dirs, files in os.walk('corpus'):
            for fname in files:
                # link topic to document indices
                topic_str = root.split('/')[-1]
                if topic_str not in topic_dict:
                    topic_dict[topic_str] = [doc_idx]
                else:
                    topic_dict[topic_str].append(doc_idx)
                document_topic_str_dict[doc_idx] = topic_str
                doc_idx += 1

                # process document
                path = os.path.join(root, fname)
                with open(path, 'r', encoding='UTF-8') as f:
                    lines = f.readlines()

                    # collect doc title
                    title = lines[0].rstrip()
                    titles.append(title)

                    # collect doc vocab
                    doc_string = ''
                    for line in lines[1:]:
                        doc_string += line.rstrip() + ' '

                    # clean doc_string
                    doc_string = doc_string.lower()
                    tokens = tokenizer.tokenize(doc_string)
                    # remove stop words from tokens
                    stopped_tokens = [i for i in tokens if not i in en_stop]
                    for word in stopped_tokens:
                        stemmed_word = ps.stem(word)
                        if stemmed_word not in vocab:
                            vocab[stemmed_word] = idx
                            idx += 1

        for root, dirs, files in os.walk('corpus'):
            for fname in files:
                path = os.path.join(root, fname)
                with open(path, 'r', encoding='UTF-8') as f:
                    lines = f.readlines()

                    # collect word counts
                    word_counts = np.zeros(idx, dtype='int64')
                    doc_string = ''
                    for line in lines[1:]:
                        doc_string += line.rstrip() + ' '

                    # clean doc_string
                    doc_string = doc_string.lower()
                    tokens = tokenizer.tokenize(doc_string)
                    # remove stop words from tokens
                    stopped_tokens = [i for i in tokens if not i in en_stop]
                    for word in stopped_tokens:
                        stemmed_word = ps.stem(word)
                        word_counts[vocab[stemmed_word]] += 1
                    data.append(word_counts)

        data = np.array(data)

        # document normalization
        row_sum = np.sum(data, axis=1)[:, np.newaxis]
        data = data / row_sum
        # vocab = tuple(vocab.keys())
        # np.savez('processed_corpus.npz', data=data, vocab=vocab, titles=titles)
    else:
        loaded = np.load('processed_corpus.npz')
        data = loaded['data']
        vocab = tuple(loaded['vocab'])
        titles = list(loaded['titles'])

    # lda_func(data, vocab, titles, n_topics=9, n_top_words=12)
    return data, vocab, titles, topic_dict, document_topic_str_dict


def query(query_str, user_attribute, data, vocab, titles):
    query_vector = np.zeros(data.shape[1], dtype='int64')
    ps = PorterStemmer()
    en_stop = get_stop_words('en')
    tokenizer = RegexpTokenizer(r'\w+')
    tokens = tokenizer.tokenize(query_str)
    # remove stop words from tokens
    stopped_tokens = [i for i in tokens if not i in en_stop]
    for word in stopped_tokens:
        stemmed_word = ps.stem(word)
        query_vector[vocab[stemmed_word]] += 1

    # score = document_vec @ query_vec + w1 * user_attrib_vec + w2 * user_preference_vec
    score = data @ query_vector + 0.5 * user.user_attrib_vec + 0.5 * user.preference_vec
    sorted_index = np.argsort(score)[::-1][:5]
    titles = np.array(titles)
    result = list(titles[sorted_index])
    return result


# when user clicks a specific document, update his/her preference vector
def feedback(clicked_doc_index, user, topic_dict, document_topic_str_dict):
    # the topic string of the clicked document, e.g. "Technology"
    topic_str = document_topic_str_dict[clicked_doc_index]

    # the indices of all documents in the same topic type with the clicked document
    target_indices = topic_dict[topic_str]

    user.preference_vec[target_indices] += 0.01


class User:
    def __init__(self, corpus_size, user_attrib, username, password):
        self.preference_vec = np.zeros(corpus_size)
        self.user_attrib_vec = np.copy(user_attrib)
        self.username = username
        self.__password = password


if __name__ == '__main__':
    # preprocess corpus
    data, vocab, titles, topic_dict, document_topic_str_dict = process()

    # initialize test user object
    user_attribute = np.zeros(data.shape[0])
    user = User(data.shape[0], user_attribute, "test", "test")
    for i in range(5):
        user_attribute[i] = 0.02

    # test query
    query_result = query("he precipitating factor for the Financial Crisis of", user, data, vocab, titles)
    for i in range(len(query_result)):
        print(i + 1, query_result[i])

    # test feedback
    print("Before feedback update: \n", user.preference_vec)
    feedback(0, user, topic_dict, document_topic_str_dict)
    print("After feedback update: \n", user.preference_vec)
