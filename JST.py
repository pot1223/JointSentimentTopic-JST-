import numpy as np
import random
import tqdm
class JST:

    def __init__(self, docs, K, S, alpha, beta, gamma, iterations, paradigm_pos, paradigm_neg):

        self.docs = docs  # 문서 집합(말뭉치)

        self.V  =len(set(word for doc in docs for word in doc))  # 문서 내 단어의 총 개수 
        self.setlist = list(set(word for doc in docs for word in doc))
        self.K = K  # 토픽 수 
        self.S = S  # 감정수 (예: 긍정, 부정, 중립)

        # Paradigm Word List 
        self.paradigm_pos = paradigm_pos # 긍정 단어 모음 
        self.paradigm_neg = paradigm_neg # 부정 단어 모음 

        # 하이퍼파라미터 
        self.alpha = alpha   # 클수록 다양한 토픽, 감정이 고르게 분포  (0.5 이상이 큼, 0.1~0.01은 작음)
        self.beta = beta   
        self.gamma = gamma 

        # 반복수 
        self.iterations = iterations

        # 초기 행렬 도출 
        self._initialize_counts()


    def _initialize_counts(self):
        
        self.n_dsk = np.zeros((len(self.docs), self.S, self.K)) # 문서수 by 감정 수 by 토픽 수 
        
        self.n_skw = np.zeros((self.S, self.K, self.V)) # 감정 수 by 토픽 수 by 문자 수 
        
        self.n_sk = np.zeros((self.S, self.K)) # 감정 수  by 토픽 수 
        
        self.n_ds = np.zeros((len(self.docs), self.S)) # 문서수 by 감정 수 

        self.topic_assignments = []  
        self.sentiment_assignments = []  

        # 문서별로 감정과 주제를 초기화
        for d, doc in enumerate(self.docs):
            current_topics = []
            current_sentiments = []
            for i, word in enumerate(doc):
                if word in self.paradigm_pos:
                    s = 0 # 긍정 할당
                elif word in self.paradigm_neg:
                    s = 1 # 부정 할당   
                else:
                    s = np.random.randint(0, self.S)  # paradigm에 속하지 않은 단어에 대해  감정을 랜덤 초기화 할당 
                k = np.random.randint(0, self.K)  # 모든 단어에 대해 주제를 랜덤 초기화 할당 
                current_sentiments.append(s)
                current_topics.append(k)
                w = self.setlist.index(word)

                # 카운트 초기화
                self.n_dsk[d][s][k] += 1
                self.n_skw[s][k][w] += 1
                self.n_sk[s][k] += 1
                self.n_ds[d][s] += 1
         
            self.topic_assignments.append(current_topics) 
            self.sentiment_assignments.append(current_sentiments)
           
    
       
    def _sample(self, d, i):
        current_topic = self.topic_assignments[d][i]
        current_sentiment = self.sentiment_assignments[d][i]
       
        # 기존 값 제거 (감정과 주제 할당을 업데이트하기 전)
        if self.n_dsk[d][current_sentiment][current_topic] > 0:
            self.n_dsk[d][current_sentiment][current_topic] -= 1

        w = self.setlist.index(self.docs[d][i])

        if self.n_skw[current_sentiment][current_topic][w] > 0:
            self.n_skw[current_sentiment][current_topic][w] -= 1
        if self.n_sk[current_sentiment][current_topic] > 0:
            self.n_sk[current_sentiment][current_topic] -= 1
        if self.n_ds[d][current_sentiment] > 0:
            self.n_ds[d][current_sentiment] -= 1

        # 새로운 감정과 주제 샘플링
        probabilities = np.zeros((self.S, self.K))
        for s in range(self.S):
            for k in range(self.K):
                
                # 감정-주제-단어 확률
                left_term = (self.n_skw[s][k][w] + self.beta) / (self.n_sk[s][k] + self.V * self.beta)
                # 문서-감정-주제 확률
                middle_term = (self.n_dsk[d][s][k] + self.alpha) / (self.n_ds[d][s] + self.K * self.alpha)
                # 감정 확률
                right_term = (self.n_ds[d][s] + self.gamma) / (len(self.docs[d]) + self.S * self.gamma)
              
                probabilities[s][k] = left_term * middle_term * right_term  # p(s,k | d,w)
       

        # 확률에 따라 새로운 감정과 주제를 샘플링
        probabilities = probabilities.flatten()
        chosen_idx = np.random.choice(np.arange(len(probabilities)), p=probabilities / probabilities.sum())
        new_sentiment, new_topic = divmod(chosen_idx, self.K)


        # 카운트 업데이트
        self.n_dsk[d][new_sentiment][new_topic] += 1
        self.n_skw[new_sentiment][new_topic][w] += 1
        self.n_sk[new_sentiment][new_topic] += 1
        self.n_ds[d][new_sentiment] += 1

        return new_sentiment, new_topic


    def _compute_distributions(self):
        # 감정-주제-단어 분포
        phi = (self.n_skw + self.beta) / (self.n_sk[:, :, np.newaxis] + self.V * self.beta)
        # 문서-감정-주제 분포 
        theta = (self.n_dsk + self.alpha) / (self.n_ds[:, :, np.newaxis] + self.K * self.alpha)
        # 문서-감정 분포 
        pi = (self.n_ds + self.gamma) / (np.sum(self.n_ds, axis=1)[:, np.newaxis] + self.S * self.gamma)
        return phi, theta, pi, self.setlist


    def run(self):
        for iteration in tqdm.tqdm(range(self.iterations)):
            for d, doc in enumerate(self.docs):
                for i, word in enumerate(doc):
                    new_sentiment, new_topic = self._sample(d, i)
                    self.sentiment_assignments[d][i] = new_sentiment
                    self.topic_assignments[d][i] = new_topic
        return self._compute_distributions()  

# ============================================================================================================================  #




paradigm_pos = positive # 각 긍정 및 부정 단어도 토큰화 수행 

paradigm_neg = negative


# 하이퍼 파라미터 알파, 베타, 감마는 클수록 다양한 토픽, 감정이 고르게 분포  (0.5 이상이 큼, 0.1~0.01은 작음)
# K : 토픽 수, S : 감정 수 
jst = JST(docs=filtered_ride_document_vector, K=6, S = 2, alpha=0.5, beta=0.5, gamma= 0.5, iterations=50, paradigm_pos = paradigm_pos,  paradigm_neg= paradigm_neg)   
phi, theta, pi, set_list = jst.run()


print("Sentiment-Topic-Word Distribution (Phi)")
print("Document-Sentiment-Topic Distribution (Theta)")
print("Document-Sentiment Distribution (pi)")

# ============================================================================================= # 

 # 해석 # 

indexed_list = list(enumerate(phi[1][5]))

# 값에 따라 내림차순으로 정렬
sorted_indexed_list = sorted(indexed_list, key=lambda x: x[1], reverse=True)

# 상위 20개의 값과 인덱스를 추출
top_20_with_index = sorted_indexed_list[:20]

for index, value in top_20_with_index:
    print(f"Index: {index}, Word: {word_lst[index]}, Value: {value}")





positive_lst = [0]*6 # 토픽 수 입력
for i in range(len(theta)):
    positive_lst += theta[i][0]    

# 토픽별 긍정 확률
topic_positive =   positive_lst / len(theta)


negative_lst = [0] * 6 # 토픽 수 입력
for i in range(len(theta)):
    negative_lst  += theta[i][1]    

# 토픽별 부정 확률
topic_negative = negative_lst  / len(theta)

for k in range(6): # 토픽 수 입력
    if topic_positive[k] > topic_negative[k]:
        print(topic_positive[k])
        print(topic_negative[k])
        print(f"토픽 {k}는 긍정")
    else:
        print(topic_positive[k])
        print(topic_negative[k])
        print(f"토픽 {k}는 부정")

# ========================================================================================== # 
# 일관성 점수 


from itertools import combinations
from collections import Counter
import numpy as np

def _compute_coherence(top_n=10, phi=None, set_list=None, docs=None, S=2, K=4, epsilon=1e-10):
    if phi is None or set_list is None or docs is None:
        raise ValueError("phi, set_list, and docs must be provided")

    # Create a dictionary that counts word occurrences in documents
    word_count = Counter(word for doc in docs for word in doc)
    
    # Create a dictionary that counts co-occurrences of word pairs in documents
    pair_count = Counter()
    for doc in docs:
        unique_words = set(doc)
        for pair in combinations(unique_words, 2):
            pair_count[tuple(sorted(pair))] += 1
    
    total_docs = len(docs)
    topic_coherence_scores = []

    # Compute coherence for each topic
    for s in range(S):
        for k in range(K):
            # Get the top N words for the current topic
            top_words_indices = np.argsort(phi[s, k])[-top_n:]
            top_words = [set_list[i] for i in top_words_indices]

            # Avoid duplicate word pairs across topics
            unique_top_words = list(set(top_words))

            # Calculate the coherence score for the current topic
            score = 0
            pair_count_in_topic = 0
            for w1, w2 in combinations(unique_top_words, 2):
                # Calculate P(w1, w2) / (P(w1) * P(w2)) for each pair
                w1_count = word_count[w1]
                w2_count = word_count[w2]
                pair_key = tuple(sorted((w1, w2)))
                pair_occurrence = pair_count[pair_key]

                if pair_occurrence > 0 and w1_count > 0 and w2_count > 0:
                    p_w1 = (w1_count + epsilon) / total_docs
                    p_w2 = (w2_count + epsilon) / total_docs
                    p_w1_w2 = (pair_occurrence + epsilon) / total_docs
                    score += np.log((p_w1_w2) / (p_w1 * p_w2))
                    pair_count_in_topic += 1

            # Only average if there are valid pairs
            if pair_count_in_topic > 0:
                score /= pair_count_in_topic  # Average over pairs

            topic_coherence_scores.append(score)

    # Normalize the coherence score across all topics
    avg_coherence_score = np.mean(topic_coherence_scores)
    
    return avg_coherence_score
