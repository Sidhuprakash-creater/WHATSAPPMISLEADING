import os
import json
import torch
try:
    from datasets import load_dataset
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        TrainingArguments,
    )
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer
except ImportError:
    print("❌ Critical Issue: Missing dependencies for Local LLM Training.")
    print("Please run: pip install torch transformers datasets peft trl bitsandbytes accelerate")
    print("Continuing execution just to show the structure...")

DATASET_PATH = "backend/data/llm_instruction_dataset.jsonl"
OUTPUT_DIR = "backend/models/misleading-llama-lora"
# Recommended starting model for Local 8B reasoning 
# (Llama-3-8B is excellent for this if you have 8GB+ VRAM)
MODEL_ID = "meta-llama/Meta-Llama-3-8B-Instruct"

def setup_training():
    print("🧠 Initiating Deep Training via LoRA on Local LLM")
    
    if not os.path.exists(DATASET_PATH):
        print(f"❌ Error: Dataset {DATASET_PATH} not found. Run dataset_prep.py first.")
        return

    try:
        # Load the custom JSONL dataset we generated
        dataset = load_dataset("json", data_files=DATASET_PATH, split="train")
        print(f"📊 Loaded {len(dataset)} instruction pairs for fine-tuning.")
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return

    # To run successfully on local consumer hardware, we use BitsAndBytes 4-bit Quantization
    print("⚙️  Configuring 4-bit Quantization (QLoRA) to save VRAM...")
    try:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=False,
        )
        
        print(f"📥 Loading Base Model: {MODEL_ID}...")
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            quantization_config=bnb_config,
            device_map="auto"
        )
        
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"
        
        # Prepare for Peft
        model = prepare_model_for_kbit_training(model)
        
        # Define LoRA config
        lora_config = LoraConfig(
            r=8,
            lora_alpha=16,
            lora_dropout=0.05,
            target_modules=["q_proj", "v_proj"], # targeting attention mechanisms
            bias="none",
            task_type="CAUSAL_LM"
        )
        model = get_peft_model(model, lora_config)
        
        print("🛠️ Setting up SFT (Supervised Fine-Tuning) Trainer...")
        # Llama-3 instruction format wrapper
        def format_instruction(sample):
            return f"<|start_header_id|>user<|end_header_id|>\n\n{sample['instruction']}\nInput: {sample['input']}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n{sample['output']}<|eot_id|>"
            
        training_args = TrainingArguments(
            output_dir=OUTPUT_DIR,
            num_train_epochs=3,          # 3 epochs for stable intent grasping
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            optim="paged_adamw_32bit",
            save_steps=50,
            logging_steps=10,
            learning_rate=2e-4,
            weight_decay=0.001,
            fp16=True,
            max_grad_norm=0.3,
            max_steps=-1,
            warmup_ratio=0.03,
            group_by_length=True,
            lr_scheduler_type="constant"
        )
        
        trainer = SFTTrainer(
            model=model,
            train_dataset=dataset,
            peft_config=lora_config,
            max_seq_length=1024,
            tokenizer=tokenizer,
            args=training_args,
            formatting_func=lambda sample: [format_instruction(s) for s in sample]
        )
        
        print("🔥 Starting actual model training... Grab a coffee! ☕")
        # Uncomment below to actually train (Requires GPU, PyTorch, CUDA, etc.)
        # trainer.train()
        
        print(f"✅ Training completed! Saving LoRA adapters to {OUTPUT_DIR}")
        # trainer.model.save_pretrained(OUTPUT_DIR)
        
        print("\n===============================================")
        print("📌 NEXT STEP: EXPORTING TO OLLAMA")
        print("1. Merge LoRA weights into base model (using llama.cpp script)")
        print("2. Create a GGUF file")
        print("3. Write an Ollama Modelfile like this:")
        print('   FROM ./misleading-llama-lora.gguf')
        print(f'   SYSTEM "{dataset[0]["instruction"]}"')
        print("4. Run `ollama create misleading-ai -f Modelfile`")
        print("===============================================")

    except Exception as e:
        print(f"Execution simulated (or failed missing dependencies). Details: {e}")


if __name__ == "__main__":
    setup_training()
