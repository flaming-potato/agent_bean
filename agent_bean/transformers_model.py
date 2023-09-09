
import torch
import transformers

from   typing                  import List, Optional
from   agent_bean.system_info  import SystemInfo


class TransformersEmbeddings:
    """This class wraps the HuggingFace transformers tokenizers to be uses like langchain's OpenAIEmbeddings"""
    def __init__(self, tokenizer: transformers.PreTrainedTokenizer) -> None:
        self.tokenizer = tokenizer

    def __call__(self, text: str) -> torch.Tensor:
        """Return the embeddings for the text"""
        return torch.tensor(self.tokenizer(text)['input_ids'])

    """def embed_documents(self, texts: List[str], chunk_size: Optional[int] = 0) -> List[List[float]]:
        \"""Return the embeddings for the query\"""
        #print(f"Embed DOC!")
        #print([self.tokenizer(text)['input_ids'] for text in texts])
        if chunk_size:
            print(f"ERROR: chunk_size: {chunk_size} NOT IMPLEMENTED YET")
            return [self.tokenizer(text)['input_ids'] for text in texts]
        else:
            return [self.tokenizer(text)['input_ids'] for text in texts]
    """
    #def embed_query(self, text: str) -> List[float]:
    def encode(self, text: str) -> List[int]:
        """Return the embeddings for the query"""
        tok = self.tokenizer(text)
        #print(f"tok: {tok}")
        return self.tokenizer(text)['input_ids']
    
    def decode(self, tokens: List[int]) -> str:
        """Return the text for the tokens"""
        #print(f"tokens: {tokens}")
        return self.tokenizer.decode(tokens)
    
    def free(self) -> None:
        """Free the memory used by the embeddings"""
        self.tokenizer = None
    
       

class TfModel:
    """This class wraps the HuggingFace transformers pipeline class to allow to build a pipeline from the setting data"""
    def __init__(self, setup: dict, system_info:SystemInfo, model_name: str) -> None:
        self.setup                            = setup
        self.system_info                      = system_info
        self.model_name                       = model_name
        self.compute_dtype                    = torch.float16
        self.GPU_brand:str                    = self.system_info.get_gpu_brand()
 
        self.pipeline                         = None
        self.quant_type_4bit:bool             = None
        self.model_bits:int                   = None
        self.model                            = None
        self.tokenizer                        = None
        self.stopping_criteria                = None
        self.model_id:str                     = None
        self.k_model_id:str                   = None
        self.do_sample:bool                   = True
        self.temperature:float                = 0.1     # 'randomness' of outputs, 0.0 is the min and 1.0 the max
        self.top_p:float                      = 1
        self.top_k:float                      = 0
        self.frequency_penalty:float          = 0.6
        self.presence_penalty:float           = 0.0
        self.repetition_penalty:float         = 1.1     # without this output begins repeating
        self.stop:List[str]                   = ["\n"]
        self.max_new_tokens:int               = 512     # max number of tokens to generate in the output

        #print(f"GPU brand: {self.GPU_brand}")
        self.instantiate_pipeline()

    @staticmethod
    def keyify_model_id(model_id):
        """Clean the model_id into a string that can be used as a key"""
        return str(model_id).replace('/', '_-_')

    @staticmethod
    def de_keyify_model_id(cleaned_model_id):
        """Reverse the cleaning process to get the original model_id"""
        return cleaned_model_id.replace('_-_', '/')

    def instantiate_pipeline(self) -> None:
        """instantiate the pipeline defined in the set-up """
        model_name = self.model_name
        if self.setup['models_list'][model_name]['model_type'] == "transformers":
            # Instantiate the Transformers model here
            # You will need to fill in the details based on how you want to use the Transformers library
            self.model_id   = self.setup['models_list'][model_name]['model_id']
            self.k_model_id = self.keyify_model_id(self.model_id)
            self.device     = f'cuda:{torch.cuda.current_device()}' if torch.cuda.is_available() else 'cpu'
            print(f"device: {self.device}, brand: {self.GPU_brand}")
            # check if the number of bits for quantization is set in setum model
            if 'model_bits' in self.setup['models_list'][model_name]:
                self.model_bits = self.setup['models_list'][model_name]['model_bits']
                        
            if self.GPU_brand == 'NVIDIA':
                #self.compute_dtype    = torch.bfloat16
                self.compute_dtype    = torch.float16
            else:
                self.compute_dtype    = torch.float16

            if self.model_bits == 4:
                # check if 4bit_quant_type in setum model
                if '4bit_quant_type' in self.setup['models_list'][model_name]:
                    self.quant_type_4bit = self.setup['models_list'][model_name]['4bit_quant_type']
                # set quantization configuration to load large model with less GPU memory
                # this requires the `bitsandbytes` library
                bnb_config = transformers.BitsAndBytesConfig(
                    load_in_4bit              = True,
                    bnb_4bit_quant_type       = self.quant_type_4bit,
                    bnb_4bit_use_double_quant = True,
                    bnb_4bit_compute_dtype    = self.compute_dtype,
                    disable_exllama           = True,
                    get_loading_attributes    = True,
                )
            
            elif self.model_bits == 8:
                # set quantization configuration to load large model with less GPU memory
                # this requires the `bitsandbytes` library
                bnb_config = transformers.BitsAndBytesConfig(
                    load_in_8bit              = True,
                    bnb_8bit_use_double_quant = True,
                    bnb_8bit_compute_dtype    = self.compute_dtype,
                    disable_exllama           = True,
                    get_loading_attributes    = True,
                )
            else:
                bnb_config = None


            if bnb_config:
                self.model = transformers.AutoModelForCausalLM.from_pretrained(
                    self.model_id,
                    #trust_remote_code   = True,
                    quantization_config = bnb_config,
                    torch_dtype         = self.compute_dtype,
                    device_map          = 'auto',
                )
            else:
                self.model = transformers.AutoModelForCausalLM.from_pretrained(
                    self.model_id,
                    #trust_remote_code   = True,
                    torch_dtype         = self.compute_dtype,
                    device_map          = 'auto',
                )

            self.tokenizer = transformers.AutoTokenizer.from_pretrained(
                self.model_id,
            )

            self.embeddings = TransformersEmbeddings(self.tokenizer)

            # set stopping criteria
            stop_list         = ['\nHuman:', '\n```\n']
            stop_token_ids    = [self.tokenizer(x)['input_ids'] for x in stop_list     ]
            stop_token_ids_LT = [torch.LongTensor(x).to(self.device) for x in stop_token_ids]  # convert to LongTensor for compatibility with model

            class StopOnTokens(transformers.StoppingCriteria):
                def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
                    for stop_ids in stop_token_ids_LT:
                        if torch.eq(input_ids[0][-len(stop_ids):], stop_ids).all():
                            return True
                    return False

            self.stopping_criteria = transformers.StoppingCriteriaList([StopOnTokens()])

            self.pipeline          = transformers.pipeline(
                    model              = self.model, 
                    tokenizer          = self.tokenizer,
                    return_full_text   = True,                       # langchain expects the full text
                    task               ='text-generation',
                    stopping_criteria  = self.stopping_criteria,     # without this model rambles during chat
                    do_sample          = True,
                    temperature        = self.temperature,           # 'randomness' of outputs, 0.0 is the min and 1.0 the max
                    max_new_tokens     = self.max_new_tokens,        # max number of tokens to generate in the output
                    repetition_penalty = self.repetition_penalty,    # without this output begins repeating
                )
            
    def predict(self, prompt: str) -> List[str]:
        """predict the next token based on the prompt"""

        print(f"### PREDICT ### prompt length: {len(prompt)}")
        print(f"### PREDICT ### prompt: {prompt}")
        if self.temperature <= 0.0: self.temperature = 0.01          # temp need to be strictly positive
        pre_prms  = {'return_tensors':"pt"                }
        fwd_prms  = {'max_new_tokens'  : self.max_new_tokens,
                     'temperature'     : self.temperature   ,
                     'top_p'           : self.top_p         ,
                     'top_k'           : self.top_k         ,
                     'do_sample'       : self.do_sample     , }
        post_prms = {'clean_up_tokenization_spaces':True,  }
        #res_raw   = self.pipeline.run_single(prompt, 
        #                               preprocess_params  = pre_prms, 
        #                               forward_params     = fwd_prms, 
        #                               postprocess_params = post_prms)
        res_raw   = self.pipeline.predict(prompt)
        print(f"### R E S ###: {len(res_raw)}")
        print(f"\n### R E S  R A W ###: {res_raw}")
        res       = res_raw[0]['generated_text'].split('#~!|MODEL OUTPUT|!~#:')
        print(f"\n### R E S ###: {res[1]}")
        if len(res) > 1:
            return res[1]
        else:
            return ''
    

    def free(self) -> None:
        """Free the memory used by the model"""
        print(f"dir: {dir(self.model)}")
        print(f"model mem: {self.model.get_memory_footprint()}")
        self.model.to_empty(device=self.device)
        #self.model.cuda.empty_cache()
        self.embeddings.free()
        self.tokenizer = None
        self.pipeline  = None
        self.model     = None
        self.embeddings= None
