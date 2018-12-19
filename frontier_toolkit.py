import lda
import lda.datasets
import numpy as np
import os
from nltk.stem import PorterStemmer
from nltk.tokenize import RegexpTokenizer
from stop_words import get_stop_words
import re


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
        topic_words = np.array(vocab)[np.argsort(topic_dist)][:-(n_top_words + 1):-1]
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
        document_bodies = []

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
                topic_str = re.split(r'[/]|[\\\]]', root)[-1]
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

                    document_bodies.append(doc_string)

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
    return data, vocab, titles, topic_dict, document_topic_str_dict, document_bodies


def query(query_str, user, data, vocab, titles, document_bodies):
    query_vector = np.zeros(data.shape[1], dtype='int64')
    ps = PorterStemmer()
    en_stop = get_stop_words('en')
    tokenizer = RegexpTokenizer(r'\w+')
    tokens = tokenizer.tokenize(query_str)
    # remove stop words from tokens
    stopped_tokens = [i for i in tokens if not i in en_stop]
    match = False
    for word in stopped_tokens:
        stemmed_word = ps.stem(word)
        if stemmed_word in vocab:
            match = True
            query_vector[vocab[stemmed_word]] += 1

    if match:
        # score = document_vec @ query_vec + w1 * user_attrib_vec + w2 * user_preference_vec
        score = data @ query_vector + 0.5 * user.user_attrib_vec + 0.5 * user.preference_vec
        sorted_index = np.argsort(score)[::-1][:5]
        titles = np.array(titles)
        document_bodies = np.array(document_bodies)
        return list(titles[sorted_index]), list(document_bodies[sorted_index]), list(sorted_index)
    else:
        return [], [], []


# when user clicks a specific document, update his/her preference vector
def feedback(clicked_doc_index, user, topic_dict, document_topic_str_dict):
    print("update feedback for user", user.username, "for document", clicked_doc_index)

    # the topic string of the clicked document, e.g. "Technology"
    topic_str = document_topic_str_dict[clicked_doc_index]

    # the indices of all documents in the same topic type with the clicked document
    target_indices = topic_dict[topic_str]

    user.preference_vec[target_indices] += 0.002


class User:
    def __init__(self, preference, user_attrib, username, password):
        self.preference_vec = np.copy(preference)
        self.user_attrib_vec = np.copy(user_attrib)
        self.username = username
        self.__password = password

    # simple login check
    def login(self, password):
        return password == self.__password


class Authenticator:
    def __init__(self, corpus_size, topic_dict, document_topic_str_dict):
        self.username_to_user_dict = {}
        self.current_username = ""
        self.occupation_topic_dict = {"Teacher": "Education", "Model": "Fashion", "Accountant": "Finance",
                                      "Chef": "Food", "Doctor": "Health", "Officer": "Politics",
                                      "Athlete": "Sport", "Software Engineer": "Technology", "Traveller": "Travel"}
        self.corpus_size = corpus_size
        self.topic_dict = topic_dict
        self.document_topic_str_dict = document_topic_str_dict

    def register(self, username, password, occupation):
        if username in self.username_to_user_dict:
            return "Error: Username is already taken, please try another username."
        elif occupation not in self.occupation_topic_dict:
            return "Error: Please select a valid occupation."
        elif not username or not password:
            return "Error: username and password cannot be empty."
        else:
            preference_vec = np.zeros(self.corpus_size)
            user_attrib_vec = np.zeros(self.corpus_size)
            topic_str = self.occupation_topic_dict[occupation]
            target_indices = self.topic_dict[topic_str]
            user_attrib_vec[target_indices] = 0.1

            new_user = User(preference_vec, user_attrib_vec, username, password)
            self.username_to_user_dict[username] = new_user
            return "Successfully create user"

    def login(self, username, password):
        if username not in self.username_to_user_dict:
            return "Error: Username does not exist."
        elif self.current_username != "":
            return "Error: Someone else is currently logged in."
        else:
            temp_user = self.username_to_user_dict[username]
            # if password is wrong
            if not temp_user.login(password):
                return "Error: Incorrect password."
            else:
                self.current_username = username
                return "Successfully logged in."

    def logout_current_user(self):
        self.current_username = ""

    def get_current_login_user(self):
        if self.current_username != "":
            return self.username_to_user_dict[self.current_username]
        else:
            raise Exception("Not logged in")


if __name__ == '__main__':
    # preprocess corpus
    data, vocab, titles, topic_dict, document_topic_str_dict, document_bodies = process()

    # initialize Authenticator for the system
    auth = Authenticator(data.shape[0], topic_dict, document_topic_str_dict)

    # register test user
    username, password, occupation = "test_user", "test_password", "Athlete"
    message = auth.register(username, password, occupation)
    print(message)

    # login test user
    message = auth.login(username, password)
    print(message)

    try:
        user = auth.get_current_login_user()
    except Exception as inst:
        print(inst)

    # test query
    result_titles, result_bodies, result_idx = query("he precipitating factor for the Financial Crisis of", user, data, vocab,
                                         titles, document_bodies)
    for i in range(len(result_titles)):
        print(i + 1, result_titles[i])

    # test feedback
    print("Before feedback update: \n", user.preference_vec)
    feedback(0, user, topic_dict, document_topic_str_dict)
    print("After feedback update: \n", user.preference_vec)
