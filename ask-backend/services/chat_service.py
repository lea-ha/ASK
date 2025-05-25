from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings, OpenAI
import uuid
import os
import logging
import json

logger = logging.getLogger(__name__)

class ChatService:

    def __init__(self):
        self.sessions = {}  # In memory storage for demo (will store the different pdfs uploaded)
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(temperature=0.2, model="gpt-3.5-turbo")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200, 
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        self.chat_history = []

    def store_document(self, text, file_name):
        try:
            session_id = str(uuid.uuid4())
            chunks = self.text_splitter.split_text(text)

            if not chunks:
                logger.error(f"No chunks were generated from the text for {file_name}")
                return None
            
            # Create unique persist directory for this session
            persist_directory = f"./chroma_db/session_{session_id}"
            
            # Create ChromaDB vector store using Langchain's Chroma wrapper
            # This approach doesn't require managing ChromaDB client directly
            vector_store = Chroma.from_texts(
                texts=chunks,
                embedding=self.embeddings,
                metadatas=[{'source': file_name} for _ in chunks],
                persist_directory=persist_directory
            )
            
            # Persist the vector store
            vector_store.persist()
            
            # Create a RetrievalQA chain
            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 3}
            )
            chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=retriever
            )

            # Store the session
            self.sessions[session_id] = {
                "chain": chain,
                "vector_store": vector_store,
                "file_name": file_name,
                "chunks": chunks,
                "persist_directory": persist_directory
            }
            
            logger.info(f"Document stored with session_id: {session_id}")
            return session_id
                
        except Exception as e:
            logger.error(f"Error storing document: {e}")
            raise Exception(f"Failed to store document: {str(e)}")
    
    def load_existing_session(self, session_id, persist_directory):
        """Load an existing session from disk"""
        try:
            if os.path.exists(persist_directory):
                vector_store = Chroma(
                    persist_directory=persist_directory,
                    embedding_function=self.embeddings
                )
                
                retriever = vector_store.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 3}
                )
                chain = RetrievalQA.from_chain_type(
                    llm=self.llm,
                    chain_type="stuff",
                    retriever=retriever
                )
                
                self.sessions[session_id] = {
                    "chain": chain,
                    "vector_store": vector_store,
                    "persist_directory": persist_directory
                }
                
                logger.info(f"Loaded existing session: {session_id}")
                return True
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return False
    
    def cleanup_session(self, session_id):
        """Optional: Clean up a session and its files"""
        try:
            if session_id in self.sessions:
                persist_directory = self.sessions[session_id]["persist_directory"]
                # Remove the directory and its contents
                import shutil
                if os.path.exists(persist_directory):
                    shutil.rmtree(persist_directory)
                del self.sessions[session_id]
                logger.info(f"Session {session_id} cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up session {session_id}: {e}")
    
    def ask_question(self, session_id, question):
        """Ask a question about the stored document"""
        try:
            if session_id not in self.sessions:
                raise Exception("Session not found. Please upload a document first.")
            
            session = self.sessions[session_id]
            chain = session["chain"]

            prompt = f"""
            <identity>
            You are a lecturer assistant that can answer questions about the provided document context.
            You are currently in a conversation with a student. 
            </identity>
            
            <context>
            Based on the provided document context and the chat history, please answer the student's question comprehensively and accurately.
            
            Instructions:
            - Use mainly information from the provided context
            - If the answer is not in the context, say that you don't have enough information to answer the question.
            - Provide specific examples or quotes when relevant
            - Be thorough but concise
            </context>

            <personality>
            - Be friendly and engaging
            - Be helpful and informative
            - Be concise and to the point
            </personality>
            
            <question>
            {question}
            </question>

            <chat_history>
            {self.chat_history}
            </chat_history>
            """
            
            # Get answer with sources
            result = chain.invoke({"query": prompt})
            
            answer = result["result"]

            self.chat_history.append({"role": "student", "content": question})
            self.chat_history.append({"role": "lecturer", "content": answer})
            
            # Format response with confidence
            # source_info = f"\n\n*Based on content from {session['file_name']}*"
            return f"{answer}"
                
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            raise Exception(f"Failed to answer question: {str(e)}")
    
    def generate_flashcards(self, session_id, num_cards=6):
        """Generate flashcards from the document content"""
        try:
            if session_id not in self.sessions:
                raise Exception("Session not found")
            
            session = self.sessions[session_id]
            # Get text from chunks
            text_sample = " ".join(session["chunks"][:5])[:3000]  # Use first few chunks, max 3000 chars
            
            prompt = f"""
            Based on the following academic content, create {num_cards} flashcards for studying.
            Each flashcard should have a "question" and "answer".
            Focus on key concepts, definitions, and important facts.
            Vary the question types (definitions, explanations, applications).
            
            Return as JSON with a "flashcards" array containing objects with "question" and "answer" fields.
            
            Content: {text_sample}
            """
            
            response = self.llm.predict(prompt)
            
            # Try to parse JSON response
            try:
                result = json.loads(response)
                return result.get("flashcards", [])
            except json.JSONDecodeError:
                # Fallback: create simple flashcards
                return self._create_fallback_flashcards(text_sample)
                
        except Exception as e:
            logger.error(f"Error generating flashcards: {e}")
            raise Exception(f"Failed to generate flashcards: {str(e)}")
    
    def _create_fallback_flashcards(self, text):
        """Create simple flashcards if JSON parsing fails"""
        return [
            {
                "question": "What are the main topics covered in this document?",
                "answer": "Please refer to the document summary for main topics."
            },
            {
                "question": "What are the key concepts to remember?",
                "answer": "Review the keywords section for important concepts."
            }
        ]
    
    def get_session_info(self, session_id):
        """Get information about a session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            return {
                "filename": session["file_name"],
                "chunks_count": len(session["chunks"]),
                "status": "active",
                "persist_directory": session["persist_directory"]
            }
        return None