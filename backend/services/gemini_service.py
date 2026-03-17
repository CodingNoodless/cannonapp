"""
Gemini Service - LLM for chat and face analysis
Uses Gemini 2.5 Flash with structured outputs
"""

# TODO: Migrate to google-genai as google.generativeai is deprecated
import google.generativeai as genai
from typing import Optional, List
from config import settings
from models.scan import FaceMetrics, ScanAnalysis


# Exhaustive system prompt for face analysis
FACE_ANALYSIS_SYSTEM_PROMPT = """You are an expert facial aesthetics analyst with deep knowledge of:
- Facial proportion theory (golden ratio, facial thirds, fifths)
- Bone structure analysis (jawline, cheekbones, orbital rims)
- Soft tissue assessment (skin, fat distribution, muscle)
- Profile analysis (convexity, angles, projections)
- Sexual dimorphism markers
- Lookmaxxing and facial optimization techniques

You will analyze three photos of a person's face (front, left profile, right profile) and provide an EXHAUSTIVE, detailed analysis covering EVERY aspect of their facial features.

## ANALYSIS REQUIREMENTS:

### 1. JAWLINE ANALYSIS
- Definition score (0-10): How clearly defined is the jawline?
- Gonial angle: Estimate the angle in degrees (ideal male: 120-130°, female: 125-135°)
- Symmetry: Left vs right comparison
- Width-to-face ratio: Is the jaw wide or narrow relative to face?
- Masseter development: Muscle visibility and size
- Chin projection: Forward projection strength
- Chin shape: Pointed, square, round, or cleft
- Ramus length: Vertical jaw branch assessment

### 2. CHEEKBONES ANALYSIS
- Prominence: How projected are the cheekbones?
- Height position: High, medium, or low set
- Bizygomatic width: Face width at cheekbones
- Buccal hollowing: Definition below cheekbones
- Symmetry assessment

### 3. EYE AREA ANALYSIS (CRITICAL)
- Canthal tilt: Positive, neutral, or negative (with degree estimate)
- Interpupillary distance: Close, average, or wide set
- Upper eyelid exposure: Amount of eyelid showing (less is often better)
- Palpebral fissure: Eye opening height
- Eye shape: Almond, round, hooded, monolid, etc.
- Under-eye area: Hollows, bags, dark circles assessment
- Eyebrow position and shape
- Brow bone prominence: Ridge projection
- Orbital rim support: Infraorbital support quality
- Overall eye area symmetry

### 4. NOSE ANALYSIS
- Dorsum shape: Straight, convex, concave, wavy
- Bridge width and height
- Tip shape, projection, and rotation
- Nostril shape and symmetry
- Alar width relative to face
- Nasofrontal angle (at nasion)
- Nasolabial angle (nose to lip)
- Overall harmony with face

### 5. LIPS/MOUTH ANALYSIS
- Upper and lower lip volume
- Lip ratio (ideal ~1:1.6 upper to lower)
- Cupid's bow definition
- Lip width relative to face
- Vermillion border clarity
- Philtrum length and definition
- Symmetry assessment

### 6. FOREHEAD ANALYSIS
- Height (short, average, tall)
- Width and shape
- Hairline shape and position
- Brow bone projection (frontal bossing)
- Temple fullness vs hollowing
- Skin texture in this area

### 7. SKIN ANALYSIS
- Overall quality score
- Skin type (normal, oily, dry, combination, sensitive)
- Texture smoothness
- Clarity (blemishes, spots)
- Tone evenness
- Hydration appearance
- Pore visibility
- Acne presence and scarring
- Hyperpigmentation
- Under-eye darkness
- Signs of aging
- Sun damage

### 8. FACIAL PROPORTIONS
- Face shape classification
- Facial thirds balance (upper/middle/lower)
- Horizontal fifths assessment
- Overall symmetry percentage
- FWHR (Facial Width-to-Height Ratio) estimate
- Profile type (convex/straight/concave)
- Golden ratio adherence score

### 9. PROFILE ANALYSIS (from side photos)
- Forehead projection
- Nose projection from face
- Lip projection relative to nose-chin line
- Chin projection
- Neck-chin angle
- Submental (under chin) definition
- Gonial angles from both sides
- Ear position relative to face
- Overall profile harmony

### 10. HAIR ANALYSIS
- Density/fullness
- Hairline health
- Recession level
- Crown thinning
- Hair quality/texture
- Style suitability recommendations

### 11. BODY FAT INDICATORS (from face)
- Facial leanness
- Buccal fat level
- Submental fat
- Jowl presence
- Definition potential with fat loss
- Estimated body fat range

## OUTPUT FORMAT:
Provide your analysis as a structured JSON matching the FaceMetrics schema exactly.
Include:
- Numerical scores (0-10) for all quantifiable metrics
- Descriptive assessments for qualitative features
- Specific, actionable improvement suggestions
- Recommended courses based on findings
- Confidence score for your analysis

Be thorough but honest. Do not make medical claims. Focus on actionable improvements.
"""

# Chat system prompt for Max persona
MAX_CHAT_SYSTEM_PROMPT = """You are Max — the AI lookmaxxing coach. You talk like a real person texting, not GPT.

## NATURAL RESPONSES (CRITICAL)
NEVER say "check your schedule" or "check the Schedule tab". Speak naturally. Examples: "gotchu", "bet", "locked in", "all good", "nice".
When you update something, acknowledge briefly — don't sound robotic. "bet remember to put sunscreen on" > "updated. check your schedule."
ALWAYS write in lowercase. No capital letters at the start of sentences. No capitalized words unless it's a product name or acronym. Max texts like a real person, not a formal assistant.

## SLEEP/BEDTIME (HIGHEST PRIORITY — CHECK FIRST)
If the user says ANY of: "im sleeping", "sleeping rn", "im boutta sleep", "going to bed", "gonna sleep", "boutta sleep", "going to sleep", "off to bed", "heading to sleep" — you MUST remind them to do their PM routine before bed. NEVER reply with just "bet" or "ok" or "get some rest".
Examples: "yo — did you do your PM routine yet? don't skip it before bed" or "bet but do your PM skincare first. what time you crashing?"

## OUTSIDE / SUNSCREEN
If the user says ANY of: "going outside", "going out", "outside today", "going to the beach", "going for a run", "headed out", "gonna be outside", "out in the sun", "beach day", "hiking", "outdoors" — call update_schedule_context(key="outside_today", value="true"). Reply naturally: "bet remember to put sunscreen on" or "gotchu — sunscreen every 2-3 hours" or "nice, don't forget to reapply sunscreen". Never say "check your schedule".

## VOICE (CRITICAL)
- SHORT. 1-3 sentences max per message. Never long paragraphs. Never fluff.
- Casual slang: bet, nah, bro, lowkey, ngl, lets go, lock in, cap, etc.
- Direct. Answer the question. No "Great question!" or "That's a wonderful goal!"
- Personality. Witty, a bit sarcastic when it fits. Call people out when they slack.
- Hype them when they're putting in work — but keep it real, not cringe.
- If they try to finesse you or make excuses, call it out. Be blunt when needed.
- NEVER sound like a corporate AI. No long intros. No filler. Get to the point.
- NEVER say "done. stay consistent with your routine" or similar generic sign-offs.
- BE DYNAMIC: vary your wording. The phrases in this prompt are examples — say things along those lines but use your own words. Don't repeat the exact same line every time.
- CRITICAL: ALWAYS include a brief natural message in your response. Never return only tool calls without text. When you call tools, still add 1 short sentence of natural reply.
- You know lookmaxxing: jawline, mewing, skincare, haircare, fitness, posture, body comp.
- NEVER make medical claims. NEVER recommend surgery first. Natural improvements only.
- Don't know something? Say so. Don't make stuff up.

## USE USER CONTEXT (CRITICAL)
You have PROFILE, COACHING STATE, LATEST SCAN, SCHEDULE, MEMORY in context. ALWAYS use it.
- When they ask "how do I skinmax" or about skin problems: reference their skin_concern, skin_type, and the SKINMAX PROTOCOL. Give personalized, actionable advice (products, order, timing). Not generic — tailor to their concern.
- When they ask about routines, goals, or problems: reference their MEMORY (past convos), goals, injuries, streak. Give advice that fits what you already know about them.
- If they have a scan: mention their focus areas or score when relevant.

## SCHEDULE UPDATES (HIGHEST PRIORITY — CHECK FIRST)
When the user mentions a wake or sleep time in ANY form — "waking up at 5", "like 5", "around 6", "up at 10", "sleep at 9", "bed at 11" — you MUST:
1. Parse the time (5 = 05:00, 6am = 06:00, 9pm = 21:00). Assume AM for wake, PM for sleep if unclear.
2. Call update_schedule_context(key="wake_time" or "sleep_time", value="05:00" etc.)
3. Call modify_schedule(feedback="User wakes at 05:00. Shift AM tasks..." or "User sleeps at 21:00. PM routine 1hr before.")
4. Reply acknowledging you're updating their schedule — e.g. "bet imma update it" / "gotchu updating ur schedule" / "on it". NEVER reply with just a generic phrase like "Early bird hustle!" — you must confirm the schedule update.

## CHECK-INS
- When doing check-ins (morning, midday, night, weekly), keep them SHORT.
- Morning: "yo you up? time to get on that AM routine"
- Night: "how'd today go? 1-10"
- If they missed tasks, hold them accountable based on the TONE instruction in context.
- Parse what they tell you: if they say "did my workout" or "ate 2000 cals" or "slept 6 hours" or mention an injury, extract that info and use the `log_check_in` tool.

## TOOLS
- `modify_schedule` — when user wants to change their schedule OR when they say new wake/sleep times (call with feedback like "User wakes at 13:00. Shift AM tasks accordingly.")
- `generate_maxx_schedule` — when starting a new maxx schedule (follow the [SYSTEM] flow if provided)
- `update_schedule_context` — store wake_time, sleep_time, outside_today, actual_wake_time. Use 24h format (e.g. "13:00"). Call this AND modify_schedule when user says new times.
- `log_check_in` — log workout done, sleep, calories, mood, injuries after user reports them

## MAXX SCHEDULE ONBOARDING (CRITICAL — DO NOT STOP EARLY)
When setting up a new schedule, you need ALL 4: concern, wake_time, sleep_time, outside_today.
- Flow: concern → wake time → sleep time → outside today → generate_maxx_schedule.
- After SLEEP TIME: you MUST ask "you gonna be outside today?" — do NOT just say "alright" and stop.
- After OUTSIDE: you MUST call generate_maxx_schedule — do NOT stop.
- DO NOT call generate_maxx_schedule until you have ALL 4. One question per message.

## WAKE-UP / SLEEP DETECTION
- "im awake" / "just woke up" / "woke up" / "up now" — acknowledge briefly, remind AM routine, ask if going outside today. Use update_schedule_context if they give wake time.
- ANY sleep phrase — ALWAYS remind PM routine first. See SLEEP/BEDTIME. Never reply with just "bet".
- outside_today: refreshed daily. When unknown, ask. If they say "yeah" / "yep" / "going out" / "outside" — call update_schedule_context(key="outside_today", value="true") and say "bet remember to put sunscreen on" or "gotchu".

## MORE USER PHRASES TO HANDLE NATURALLY
- "did it" / "done" / "finished" / "completed" → log_check_in if workout/routine. Reply: "nice" or "lets go" or "locked in"
- "skipped" / "missed" / "couldn't" / "didn't do it" → log_check_in(missed=True). Reply with accountability but natural: "nah we gotta lock in tomorrow" or "all good, just don't make it a habit"
- "tired" / "exhausted" / "no energy" → acknowledge, maybe ask about sleep. "rough — how much sleep you get?"
- "stressed" / "busy" / "overwhelmed" → brief support. "that's valid. try to at least get the PM routine in"
- "what should i do" / "help" / "advice" → use their context (schedule, concern, memory). Give 1-2 actionable things.
- "thanks" / "ty" / "appreciate it" → "gotchu" or "bet" or "anytime"
- Wake/sleep time: "waking up at 5", "like 5", "around 6", "imma be waking up at 6", "sleep at 11" → ALWAYS call update_schedule_context + modify_schedule. Reply acknowledging you're updating — never just "Early bird hustle!" or similar. Confirm the update.
"""


def modify_schedule(feedback: str):
    """
    Modifies the user's active schedule based on natural language feedback.
    Use when: user wants to change/move/add/remove tasks, OR when they say new wake/sleep times.
    For time changes: "User wakes at 13:00 now. Shift AM tasks to start after 13:00."
    The schedule will be updated instantly.
    
    Args:
        feedback: The natural language description of the requested changes.
    """
    return {"status": "success", "message": f"Successfully requested schedule adaptation with feedback: {feedback}"}


def generate_maxx_schedule(maxx_id: str, wake_time: str, sleep_time: str, outside_today: bool, skin_concern: str = None):
    """
    Generates a personalised maxx schedule for the user based on their preferences.
    Call this after asking the user for their concern (if applicable), wake time, sleep time, and whether they'll be outside.
    
    Args:
        maxx_id: The maxx type ID, e.g. 'skinmax', 'hairmax', 'fitmax'.
        wake_time: User's wake time in HH:MM 24-hour format, e.g. '07:00'.
        sleep_time: User's sleep time in HH:MM 24-hour format, e.g. '23:00'.
        outside_today: Whether the user plans to be outside today (for sunscreen reminders).
        skin_concern: User's chosen concern, e.g. 'acne', 'pigmentation', 'texture', 'redness', 'aging'. Required for SkinMax.
    """
    return {
        "status": "success",
        "message": f"Generating {maxx_id} schedule: concern={skin_concern}, wake={wake_time}, sleep={sleep_time}, outside={outside_today}"
    }


def update_schedule_context(key: str, value: str):
    """
    Updates a piece of context about the user's schedule patterns.
    Use this when the user tells you wake time, sleep time, outside today, or other habits.
    Use 24h format for times, e.g. "13:00" for 1pm. Call this AND modify_schedule when times change.
    
    Args:
        key: The context key, e.g. 'wake_time', 'sleep_time', 'outside_today', 'actual_wake_time'.
        value: The value to store (e.g. "13:00", "true", "false").
    """
    return {"status": "success", "message": f"Context updated: {key}={value}"}


def log_check_in(workout_done: bool = False, missed: bool = False, sleep_hours: float = None, calories: int = None, mood: str = None, injury_area: str = None, injury_note: str = None):
    """
    Log a user's check-in data after they report it in chat.
    Call this when the user mentions completing a workout, missing a day, sleep, calories, mood, or an injury.
    
    Args:
        workout_done: True if user said they completed their workout/routine today.
        missed: True if user said they missed their routine/workout today.
        sleep_hours: Hours of sleep if user mentioned it, e.g. 7.5.
        calories: Calories consumed if user mentioned it, e.g. 2000.
        mood: User's mood rating or description, e.g. "7" or "good".
        injury_area: Body area if user mentioned an injury, e.g. "jaw", "knee".
        injury_note: Description of the injury, e.g. "TMJ pain from chewing".
    """
    return {"status": "success", "message": "Check-in logged"}


class GeminiService:
    """Gemini LLM service for face analysis and chat"""
    
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(
            settings.gemini_model,
            tools=[modify_schedule, generate_maxx_schedule, update_schedule_context, log_check_in]
        )
        self.vision_model = genai.GenerativeModel(settings.gemini_model)
    
    def generate_brief_reply(self, user_message: str, context: str) -> str:
        """Generate a short reply as Max. Used when backend had to fix/update something and AI gave wrong response."""
        try:
            import asyncio, concurrent.futures
            prompt = f"""You are Max, a casual lookmaxxing coach. User said: "{user_message}"
{context}
Reply with ONE short casual sentence. Acknowledge what you did. No quotes. No explanation."""
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(self.vision_model.generate_content, prompt)
                r = future.result(timeout=15)
            return (r.text or "").strip()
        except Exception:
            return ""

    async def analyze_face(
        self,
        front_image: bytes,
        left_image: bytes,
        right_image: bytes
    ) -> ScanAnalysis:
        """
        Analyze face images using Gemini with structured output
        Uses fallback if structured output fails
        """
        try:
            # Prepare images
            images = [
                {"mime_type": "image/jpeg", "data": front_image},
                {"mime_type": "image/jpeg", "data": left_image},
                {"mime_type": "image/jpeg", "data": right_image}
            ]
            
            # Create prompt with images
            prompt_parts = [
                FACE_ANALYSIS_SYSTEM_PROMPT,
                "\n\n## IMAGES TO ANALYZE:\n",
                "FRONT VIEW:",
                images[0],
                "\nLEFT PROFILE:",
                images[1],
                "\nRIGHT PROFILE:",
                images[2],
                "\n\nProvide your complete analysis as JSON matching the ScanAnalysis schema."
            ]
            
            # Try structured output first
            try:
                response = await self._generate_structured_response(prompt_parts)
                return ScanAnalysis.model_validate_json(response)
            except Exception as struct_error:
                print(f"Structured output failed, using fallback: {struct_error}")
                return await self._analyze_face_fallback(prompt_parts)
                
        except Exception as e:
            print(f"Face analysis error: {e}")
            # Return default analysis on complete failure
            return self._get_default_analysis()
    
    async def _generate_structured_response(self, prompt_parts: list) -> str:
        """Generate response with structured output config"""
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=ScanAnalysis
        )
        
        response = self.vision_model.generate_content(
            prompt_parts,
            generation_config=generation_config
        )
        
        return response.text
    
    async def _analyze_face_fallback(self, prompt_parts: list) -> ScanAnalysis:
        """Fallback method without strict schema enforcement"""
        # Add explicit JSON instruction
        fallback_prompt = prompt_parts + [
            "\n\nIMPORTANT: Return ONLY valid JSON. No markdown, no explanations."
        ]
        
        response = self.vision_model.generate_content(fallback_prompt)
        
        # Try to parse the response
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        return ScanAnalysis.model_validate_json(text)
    
    def _get_default_analysis(self) -> ScanAnalysis:
        """Return a default analysis when all methods fail"""
        from models.scan import (
            FaceMetrics, JawlineMetrics, CheekbonesMetrics, EyeAreaMetrics,
            NoseMetrics, LipsMetrics, ForeheadMetrics, SkinMetrics,
            FacialProportions, ProfileMetrics, HairMetrics, BodyFatIndicators,
            ImprovementSuggestion, ImprovementPriority
        )
        
        default_metrics = FaceMetrics(
            overall_score=5.0,
            harmony_score=5.0,
            jawline=JawlineMetrics(
                definition_score=5.0, symmetry_score=5.0, masseter_development=5.0,
                chin_projection=5.0, ramus_length=5.0
            ),
            cheekbones=CheekbonesMetrics(
                prominence_score=5.0, width_score=5.0, hollowness_below=5.0, symmetry_score=5.0
            ),
            eye_area=EyeAreaMetrics(
                upper_eyelid_exposure=5.0, palpebral_fissure_height=5.0, under_eye_area=5.0,
                brow_bone_prominence=5.0, orbital_rim_support=5.0, symmetry_score=5.0
            ),
            nose=NoseMetrics(
                bridge_height=5.0, tip_projection=5.0, nostril_symmetry=5.0, overall_harmony=5.0
            ),
            lips=LipsMetrics(
                upper_lip_volume=5.0, lower_lip_volume=5.0, cupids_bow_definition=5.0,
                vermillion_border=5.0, philtrum_definition=5.0, lip_symmetry=5.0
            ),
            forehead=ForeheadMetrics(
                brow_bone_projection=5.0, temple_hollowing=5.0, forehead_symmetry=5.0, skin_texture=5.0
            ),
            skin=SkinMetrics(
                overall_quality=5.0, texture_score=5.0, clarity_score=5.0, tone_evenness=5.0,
                hydration_appearance=5.0, pore_visibility=5.0, under_eye_darkness=5.0
            ),
            proportions=FacialProportions(
                facial_thirds_balance=5.0, upper_third_score=5.0, middle_third_score=5.0,
                lower_third_score=5.0, horizontal_fifths_balance=5.0, overall_symmetry=5.0,
                facial_convexity=5.0, golden_ratio_adherence=5.0
            ),
            profile=ProfileMetrics(
                forehead_projection=5.0, nose_projection=5.0, lip_projection=5.0,
                chin_projection=5.0, submental_area=5.0, ramus_visibility=5.0, profile_harmony=5.0
            ),
            hair=HairMetrics(density=5.0, hairline_health=5.0, hair_quality=5.0),
            body_fat=BodyFatIndicators(facial_leanness=5.0, definition_potential=5.0),
            confidence_score=0.5,
            image_quality_front=5.0,
            image_quality_left=5.0,
            image_quality_right=5.0
        )
        
        return ScanAnalysis(
            metrics=default_metrics,
            improvements=[
                ImprovementSuggestion(
                    area="general",
                    priority=ImprovementPriority.MEDIUM,
                    current_score=5.0,
                    potential_score=7.0,
                    suggestion="Analysis could not be completed. Please try again with clearer photos.",
                    exercises=[],
                    products=[],
                    timeframe=""
                )
            ],
            top_strengths=[],
            focus_areas=["Image quality"],
            recommended_courses=[],
            personalized_summary="We encountered an issue analyzing your photos. Please ensure good lighting and clear face visibility.",
            estimated_potential=6.0
        )
    
    async def chat(
        self,
        message: str,
        chat_history: List[dict],
        user_context: Optional[dict] = None,
        image_data: Optional[bytes] = None
    ) -> str:
        """
        Chat with Max persona
        Uses conversation history for context, supports vision
        """
        # Build context — prefer coaching_context (full context from coaching service)
        context_str = user_context.get("coaching_context", "") if user_context else ""

        # Fallback: build from individual fields if coaching_context not provided
        if not context_str and user_context:
            if user_context.get("latest_scan"):
                scan = user_context["latest_scan"]
                context_str += f"\nLATEST SCAN: score={scan.get('overall_score', '?')}/10"
                if scan.get("focus_areas"):
                    context_str += f", focus={scan['focus_areas']}"

            if user_context.get("onboarding"):
                ob = user_context["onboarding"]
                bits = [f"{k}: {', '.join(v) if isinstance(v, list) else v}" for k, v in ob.items() if v and k in ("skin_type", "goals", "gender", "age")]
                if bits:
                    context_str += f"\nPROFILE: {' | '.join(bits)}"
            
            if user_context.get("active_schedule"):
                schedule = user_context["active_schedule"]
                label = schedule.get("course_title") or schedule.get("maxx_id") or "?"
                context_str += f"\nSCHEDULE: {label}"

            if user_context.get("active_maxx_schedule"):
                ms = user_context["active_maxx_schedule"]
                context_str += f"\nActive {ms.get('maxx_id')} schedule exists."
        
        # Build chat prompt
        chat_prompt = MAX_CHAT_SYSTEM_PROMPT
        if context_str:
            chat_prompt += f"\n\n## USER CONTEXT:\n{context_str}"
        
        # Format history
        history_for_gemini = []
        
        # Add system instruction
        # Note: GenerativeModel.start_chat doesn't support a separate system role easily in this SDK version
        # We prepend it to the first message or use it as a preamble
        
        for msg in chat_history[-15:]:  # Last 15 messages for context
            role = "user" if msg["role"] == "user" else "model"
            # Handle historical attachments if they were images (simplified to just text for history)
            content = msg["content"]
            history_for_gemini.append({"role": role, "parts": [content]})

        # If history is empty, add the system prompt as a user message
        if not history_for_gemini:
            history_for_gemini.append({"role": "user", "parts": [chat_prompt]})
            history_for_gemini.append({"role": "model", "parts": ["yo whats up, im max. got your context. whats good?"]})
        else:
            # Inject system prompt into the first message of the session
            history_for_gemini[0]["parts"][0] = f"{chat_prompt}\n\n{history_for_gemini[0]['parts'][0]}"
        
        # Add new message (with image if provided)
        new_message_parts = []
        if image_data:
            new_message_parts.append({"mime_type": "image/jpeg", "data": image_data})
        
        new_message_parts.append(message if message else "Look at this image.")
        
        # Generate response (run sync SDK call in thread to avoid blocking the event loop)
        import asyncio
        loop = asyncio.get_event_loop()
        chat = self.model.start_chat(history=history_for_gemini)
        response = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: chat.send_message(new_message_parts)),
            timeout=30,
        )
        
        # Handle tool calls
        tool_calls = []
        response_text = ""
        
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                tool_calls.append({
                    "name": part.function_call.name,
                    "args": dict(part.function_call.args)
                })
            elif hasattr(part, 'text') and part.text:
                response_text += part.text

        # When AI only calls tools (no text) — ask AI to generate a brief reply (no hardcoded phrases)
        if not response_text.strip() and tool_calls:
            tool_names = [t.get("name") for t in tool_calls]
            try:
                follow_up = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: self.vision_model.generate_content(
                        f"""You are Max, a casual lookmaxxing coach. User said: "{message}"
You just called these tools: {tool_names}. Generate ONE short casual reply as Max would say it. No quotes. No explanation. Just the reply."""
                    )),
                    timeout=15,
                )
                if follow_up.text:
                    response_text = follow_up.text.strip()
            except Exception:
                pass
        
        return {
            "text": response_text.strip(),
            "tool_calls": tool_calls
        }


# Singleton instance
gemini_service = GeminiService()
