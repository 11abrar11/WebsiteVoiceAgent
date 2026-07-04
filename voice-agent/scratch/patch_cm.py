import sys

file_path = "app/services/conversation_manager.py"
with open(file_path, "r") as f:
    content = f.read()

# 1. Imports
import_str = "from app.tools.tools import TOOL_DEFINITIONS"
new_imports = """from app.tools.tools import TOOL_DEFINITIONS
from app.services.lead_state import LeadStateManager
"""
content = content.replace(import_str, new_imports)

# 2. Init
init_str = """        self.system_prompt = ("""
new_init = """        self.lead_state = LeadStateManager(lead_id)
        self.meeting_cache = []
        self.meeting_cache_time = 0.0
        self.system_prompt = ("""
content = content.replace(init_str, new_init)

# 3. initialize_persistence
init_pers_str = """            else:
                print(">>> No lead_id provided. Running without persistence.")
        except Exception as e:"""
new_init_pers = """            else:
                print(">>> No lead_id provided. Running without persistence.")
            
            # Initialize LeadStateManager from DB
            if self.lead_id:
                await self.lead_state.load_from_db()
                
            # Start background committer task
            self._committer_task = asyncio.create_task(self._inactivity_committer())
        except Exception as e:"""
content = content.replace(init_pers_str, new_init_pers)

# 4. _inactivity_committer
inact_str = """    def _reset_metrics(self):"""
new_inact = """    async def _inactivity_committer(self):
        while not self.is_interrupted and self.state != "disconnected":
            await asyncio.sleep(10)
            if self.lead_state and self.lead_state.uncommitted_changes > 0:
                if time.time() - self.lead_state.last_update_time > 60:
                    print(">>> Inactivity timeout reached. Committing Lead State.")
                    await self.lead_state.commit()
                elif self.lead_state.uncommitted_changes >= 4:
                    print(">>> Threshold reached. Committing Lead State.")
                    await self.lead_state.commit()

    def _reset_metrics(self):"""
content = content.replace(inact_str, new_inact)

# 5. finalize_conversation
fin_str = """            # Update last_contacted on the lead"""
new_fin = """            # Commit pending lead state
            if self.lead_state:
                await self.lead_state.commit()
            self.state = "disconnected"
                
            # Update last_contacted on the lead"""
content = content.replace(fin_str, new_fin)

# 6. tool handlers
tool_str = """            if func_name == "get_available_meeting_times":
                async with AsyncSessionLocal() as session:
                    meeting_repo = MeetingRepository(session)
                    engine = MeetingEngine(meeting_repo)
                    slots = await engine.get_available_times()
                result_content = json.dumps(slots)

            elif func_name == "book_meeting":"""

new_tool = """            if func_name == "get_available_meeting_times":
                # Meeting Cache Logic (TTL = 120 seconds)
                if not self.meeting_cache or time.time() - self.meeting_cache_time > 120:
                    print(">>> Refreshing meeting cache")
                    async with AsyncSessionLocal() as session:
                        meeting_repo = MeetingRepository(session)
                        engine = MeetingEngine(meeting_repo)
                        self.meeting_cache = await engine.get_available_times()
                    self.meeting_cache_time = time.time()
                result_content = json.dumps(self.meeting_cache)

            elif func_name == "book_meeting":"""
content = content.replace(tool_str, new_tool)

# 7. book_meeting success commit
book_str = """                            args["date"], args["time"], lead_email, "Booked via AI Voice Agent"
                        ))
                        result_content = json.dumps({
                            "success": True,
                            "message": f"Meeting booked for {args['date']} at {args['time']}",
                        })"""

new_book = """                            args["date"], args["time"], lead_email, "Booked via AI Voice Agent"
                        ))
                        result_content = json.dumps({
                            "success": True,
                            "message": f"Meeting booked for {args['date']} at {args['time']}",
                        })
                        
                        # Flush lead state on successful booking
                        if self.lead_state:
                            await self.lead_state.commit()
                        # Invalidate meeting cache
                        self.meeting_cache = []"""
content = content.replace(book_str, new_book)

# 8. update_lead_info replace with extract_lead_info
extract_str = """            elif func_name == "update_lead_info":
                if self.lead_id:
                    # RATIONALE: We intentionally keep this database write synchronous.
                    # While making it asynchronous via asyncio.create_task() would reduce latency, 
                    # a synchronous write ensures strict data consistency, preventing 
                    # silent failures where the AI thinks the data was saved but the DB transaction fails.
                    # Future Enhancement: We could implement a durable transactional outbox or Redis queue
                    # to achieve low-latency without sacrificing consistency guarantees.
                    async with AsyncSessionLocal() as session:
                        repo = ConversationRepository(session)
                        await repo.update_lead(self.lead_id, args)
                    result_content = json.dumps({"success": True, "message": "Lead info updated successfully."})
                else:
                    result_content = json.dumps({"success": False, "message": "Cannot update lead - no active lead."})"""

new_extract = """            elif func_name in ["update_lead_info", "extract_lead_info"]:
                if self.lead_id:
                    self.lead_state.update_extracted_info(args)
                    result_content = json.dumps({"success": True, "message": "Lead info extracted into state manager."})
                else:
                    result_content = json.dumps({"success": False, "message": "Cannot update lead - no active lead."})"""
content = content.replace(extract_str, new_extract)

# 9. prompt injection
prompt_str = """            # Build the full prompt with returning-user context (from ContextBuilder)
            prompt = (
                f"{self.system_prompt}\\n\\n"
                f"{self.returning_context}\\n"
                f"Here are 5 relevant context chunks from our knowledge base:\\n"
                f"--- START CONTEXT ---\\n{context}\\n--- END CONTEXT ---\\n"
            )"""

new_prompt = """            # Build the full prompt with returning-user context (from ContextBuilder)
            dynamic_state = self.lead_state.get_prompt_context() if self.lead_state else ""
            prompt = (
                f"{self.system_prompt}\\n\\n"
                f"{self.returning_context}\\n"
                f"{dynamic_state}\\n"
                f"Here are 5 relevant context chunks from our knowledge base:\\n"
                f"--- START CONTEXT ---\\n{context}\\n--- END CONTEXT ---\\n"
            )"""
content = content.replace(prompt_str, new_prompt)

with open(file_path, "w") as f:
    f.write(content)

print("Patch applied successfully.")