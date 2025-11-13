import pandas as pd 
import re
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import gensim
import gensim.corpora as corpora

def topic_email_analysis(email_texts):
    # Preprocess the email texts
    stop_words = set(stopwords.words('english'))
    ps = PorterStemmer()
    
    def preprocess(text):
        text = text.lower()
        text = re.sub(r'\W', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        tokens = word_tokenize(text)
        tokens = [ps.stem(word) for word in tokens if word not in stop_words]
        return tokens
    
    processed_texts = [preprocess(email) for email in email_texts]
    
    # Create Dictionary and Corpus
    id2word = corpora.Dictionary(processed_texts)
    corpus = [id2word.doc2bow(text) for text in processed_texts]
    
    # Build LDA model
    lda_model = gensim.models.LdaModel(corpus=corpus,
                                       id2word=id2word,
                                       num_topics=5, 
                                       random_state=100,
                                       update_every=1,
                                       chunksize=10,
                                       passes=10,
                                       alpha='auto',
                                       per_word_topics=True)
    
    # Print the topics
    topics = lda_model.print_topics(num_words=5)
    for topic in topics:
        print(topic)
    return topics