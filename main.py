from openai import OpenAI

import ast
import os
from example_texts import steve_jobs_commencement_speech 
from scipy.spatial.distance import cosine
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

  prompt = """
  what are the concepts in this statement? you need to extract all fuzzy concepts that might be relevant. Make sure you're extracting *concepts* and not simply keywords that would be easily searchable.

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
  
  similarity = cosine(embed_a, embed_b)
 
  print(1-similarity)
  return (1-similarity) > threshold



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

  paragraphs = steve_jobs_commencement_speech.split("\n")
  cleaned_paragraphs = [p for p in paragraphs if p.strip() != '']
  
  for idx, p in enumerate(cleaned_paragraphs):
    
    fuzzy_concepts = extract_fuzzy_concepts(p)

    for concept in fuzzy_concepts:
      added = False
      
      embed_concept = get_embedding(concept)
      
      # for every existing concept:
      for fuzzy_concept in fuzzy_reverse_index.keys():
        # if similar enough

        print('checking similarity between ', concept, ' and ', fuzzy_concept)
  
        if is_similar(embed_concept, fuzzy_reverse_index[fuzzy_concept]["embedding"]):
          
          # add index of paragraph to that concept
          print("similar enough, so appending", idx, " to ", fuzzy_reverse_index[fuzzy_concept]["indices"])
          fuzzy_reverse_index[fuzzy_concept]["indices"].append(idx)
          added = True
      
      # otherwise, add a new concept with index
      if not added:
        fuzzy_reverse_index[concept] = {"embedding" : embed_concept, "indices": [idx]}
    # printer.pprint(fuzzy_reverse_index)





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
  return set(indices)

if __name__ == "__main__":
  # fuzzy_reverse_index = {}
  # extend_index(fuzzy_reverse_index, steve_jobs_commencement_speech)
  # save_index(fuzzy_reverse_index)

  fuzzy_reverse_index = load_index()

  for key in fuzzy_reverse_index.keys():
    print(key, fuzzy_reverse_index[key]["indices"])
  # fuzzy_reverse_index = load_index()
  print(search_fuzzy_index("on accepting death", fuzzy_reverse_index))

      





