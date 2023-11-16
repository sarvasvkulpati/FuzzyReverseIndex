from openai import OpenAI
from tqdm import tqdm
import ast
import os
from example_texts import steve_jobs_commencement_speech, startup_equals_growth
from scipy.spatial.distance import cosine
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json 
import pprint
client =OpenAI(api_key= os.environ['OPENAI_API_KEY'])


class MyPrettyPrinter(pprint.PrettyPrinter):
  def _format(self, object, stream, indent, allowance, context, level):
      if isinstance(object, str) and len(object) > 50:  # Truncating long strings
          object = object[:50] + '...'
      elif isinstance(object, list) and len(object) > 10:  # Truncating long lists
          object = object[:10] + ['...']
      pprint.PrettyPrinter._format(self, object, stream, indent, allowance, context, level)



printer = MyPrettyPrinter()



def extract_fuzzy_concepts(text):
  if len(text.split()) < 10:
    return {"concepts" :[]}
  prompt = """
  what are the concepts in this statement? you need to extract around 3-5 fuzzy concepts that might be relevant. Make sure you're extracting *concepts* and not simply keywords that would be easily searchable.

  return as a JSON list of sentences I can cast into python. It should be in this format:
  {
    "concepts": [
      "<concept>",
      "<concept>",
      "<concept>",
      "<concept>",
      "<concept>"
    ]
  }
  
  
  Don't be too vague or broad:
  """
  
  fuzzy_concepts = call_gpt(text, prompt) 
  # this line above returns an object that looks like {"concepts" : [...<concepts here>]}

  print(fuzzy_concepts)


  return ast.literal_eval(fuzzy_concepts)["concepts"]
  


def call_gpt(prompt, text):
  response = client.chat.completions.create(
      model="gpt-3.5-turbo-1106",
      response_format={ "type": "json_object" },
      messages=[
        {"role":"system", "content": prompt},
        {"role":"user", "content": text}
      ],
      temperature = 0 
  )
  response = response.choices[0].message.content
  return response



def get_embedding(text):
  response = client.embeddings.create(
    model="text-embedding-ada-002",
    input=text,
    encoding_format="float"
  )
  return response.data[0].embedding



def is_similar(embed_a, embed_b, threshold=0.9):
  
  distance = cosine(embed_a, embed_b)
  print(1-distance)
  # print(1-similarity)
  return (1-distance) > threshold



def save_index(fuzzy_reverse_index):
  filename = "fuzzy_reverse_index.json"
  with open(filename, "w") as f:
    json.dump(fuzzy_reverse_index, f, indent=4)

def load_index():
  filename = "fuzzy_reverse_index.json"
  with open(filename, "r") as f:
    fuzzy_reverse_index = json.load(f)
  return fuzzy_reverse_index

def extend_index(fuzzy_reverse_index, text):
  """
  Extends the fuzzy reverse index with the given text.
  """    

  paragraphs = text.split("\n")
  cleaned_paragraphs = [p for p in paragraphs if p.strip() != '']
  
  for idx, p in enumerate(cleaned_paragraphs):
    print(p)
    
    fuzzy_concepts = extract_fuzzy_concepts(p)

    if len(fuzzy_concepts) == 0:
      continue

    for concept in fuzzy_concepts:
      added = False
      
      embed_concept = get_embedding(concept)
      
      # for every existing concept:
      for fuzzy_concept in tqdm(fuzzy_reverse_index.keys()):
        # if similar enough

        # print('checking similarity between ', concept, ' and ', fuzzy_concept)
  
        if is_similar(embed_concept, fuzzy_reverse_index[fuzzy_concept]["embedding"]):
          
          # add index of paragraph to that concept
          print("similar enough, so appending", idx, " to ", fuzzy_reverse_index[fuzzy_concept]["indices"])
          fuzzy_reverse_index[fuzzy_concept]["indices"].append(idx)
          added = True
      
      # otherwise, add a new concept with index
      if not added:
        fuzzy_reverse_index[concept] = {"embedding" : embed_concept, "indices": [idx]}


def get_paras_by_indices(text, indices):
  for idx in indices:
    print(text.split('\n')[idx]) 


def search_fuzzy_index(query, fuzzy_reverse_index):
  query_embed = get_embedding(query)

  indices = []

  # search through fuzzy index keys for something that matches query
  for fuzzy_concept in fuzzy_reverse_index.keys():
    # print(fuzzy_concept)
    # if similarity is high enough
    if is_similar(query_embed, fuzzy_reverse_index[fuzzy_concept]["embedding"], threshold = 0.85):
      # return the indices of the paragraphs that contain that concept
      
      indices.extend(fuzzy_reverse_index[fuzzy_concept]["indices"])
  return list(set(indices))



def paragraph_data(text):
  paragraphs = text.split("\n")
  cleaned_paragraphs = [p for p in paragraphs if p.strip() != '']

  print(len(cleaned_paragraphs))
  
  p_embeddings = []

  for p in cleaned_paragraphs:
    p_embed = get_embedding(p)
    p_embeddings.append(p_embed)
  filename = "p_embeddings.json"
  
  with open(filename, "w") as f:
    json.dump(p_embeddings, f, indent=4)
  








def vector_search(query, paragraphs, p_embeddings):
  query_embed = get_embedding(query)
  
  similarities = cosine_similarity([query_embed], p_embeddings)[0]
  top_5_indices = np.argsort(similarities)[::-1][:5]
  print(len(paragraphs), len(p_embeddings))
  print(top_5_indices)
  
  return [(paragraphs[i], similarities[i]) for i in top_5_indices]
  








if __name__ == "__main__":
  # fuzzy_reverse_index = {}
  # extend_index(fuzzy_reverse_index, startup_equals_growth)
  # save_index(fuzzy_reverse_index)


  # paragraph_data(startup_equals_growth)
  

  filename = "p_embeddings.json"
  with open(filename, "r") as f:
    p_embeddings = json.load(f)

  # print(len(p_embeddings))

  paragraphs = startup_equals_growth.split("\n")
  cleaned_paragraphs = [p for p in paragraphs if p.strip() != '']

  print(vector_search("what makes startups special?", cleaned_paragraphs,p_embeddings ))

  fuzzy_reverse_index = load_index()
  
  indices = search_fuzzy_index("what makes startups special?", fuzzy_reverse_index)

  print(get_paras_by_indices(startup_equals_growth, indices))

 



