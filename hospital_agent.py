import os
import yaml
from dataclasses import dataclass, field
from typing import Annotated, Optional
from dotenv import load_dotenv
from pydantic import Field

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json
from livekit import agents
from livekit.agents import cli, WorkerOptions, AgentSession, Agent, RunContext
from livekit.agents.voice.room_io import RoomInputOptions
from livekit.agents.llm import function_tool
from livekit.plugins import (
  azure,
  openai, 
  noise_cancellation,
  silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv(".env.local")

AZURE_SPEECH_KEY = os.getenv('AZURE_SPEECH_KEY')
AZURE_SPEECH_REGION = os.getenv('AZURE_SPEECH_REGION')
AZURE_LLM_KEY = os.getenv('AZURE_LLM_KEY')
AZURE_LLM_ENDPOINT = os.getenv('AZURE_LLM_ENDPOINT')
SHEET_ID = os.getenv('SHEET_ID')
RANGE_NAME = os.getenv('RANGE_NAME')


@dataclass
class UserData:
  customer_name: Optional[str] = None
  customer_number: Optional[str] = None
  appointment_time: Optional[str] = None

  def summarize(self) -> str: 
    data = {
      "customer_name": self.customer_name or "unknown",
      "appointment_time": self.appointment_time or "unknown", 
    }
    return yaml.dump(data)

RunContext_T = RunContext[UserData]

#helper functions to read and write appointments
def get_google_sheets_service():
  creds = Credentials.from_authorized_user_file(os.getenv("TOKEN_PATH"), ["https://www.googleapis.com/auth/spreadsheets"])
  service = build('sheets', 'v4', credentials=creds)
  return service

def get_appointments(sheet_id, range_name):
  service = get_google_sheets_service()
  sheet = service.spreadsheets()
  result = sheet.values().get(spreadsheetId=sheet_id, range=range_name).execute()
  values = result.get('values', [])
  return values


def add_appointment(sheet_id, range_name, name, appointment_time):
  print("add_appointment called with:", name, appointment_time)
  print("Types:", type(name), type(appointment_time))
  service = get_google_sheets_service()
  sheet = service.spreadsheets()
  sheet.values().append(
      spreadsheetId=sheet_id,
      range=range_name,
      valueInputOption="RAW",
      body={"values": [[str(name), str(appointment_time)]]}
  ).execute()

class Assistant(Agent):
  def __init__(self) -> None: 
    super().__init__(instructions="You are a receptionist at a hospital. " \
    "Your job is to book appointments for users. Ask their name and book an appointment for them" \
    "You also need to make sure the appointments " \
    "that users make don't clash with an existing appointment.")
  
  #tool to update name
  @function_tool()

  async def update_name(
    self,
    username: Annotated[str, Field(description="The customer's name")],
    context: RunContext_T,
  ) -> str:
    """Called when the user provides their name
    Confirm the spelling with the user before calling the function."""

    userdata = context.userdata
    userdata.customer_name = username
    return f"The name is updated to {username}"

  #tool to make appointment
  @function_tool()
  async def make_appointment(
    self,
    appointment: Annotated[str, Field(description="Customer's appointment time")],
    context: RunContext_T,
  ) -> str:
    """Called when the user wants to make an appointment
    Confirm the appointment time with the user before calling the function"""
    userdata = context.userdata    
    print(userdata)
    userdata.appointment_time = appointment

    appointments = get_appointments(SHEET_ID, RANGE_NAME)
    for row in appointments:
      if len(row) > 1 and row[1] == appointment:
        return f"Sorry, the appointment time {appointment} is already taken."
    
    add_appointment(SHEET_ID, RANGE_NAME, str(userdata.customer_name or "unknown"), str(appointment))
    return f"The appointment was booked successfully for {appointment}"
  

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        userdata = UserData(),
        stt=azure.STT(
          speech_key = AZURE_SPEECH_KEY,
          speech_region = AZURE_SPEECH_REGION,
        ),
        llm=openai.LLM.with_azure(
          azure_deployment="gpt-5-chat",
          azure_endpoint=AZURE_LLM_ENDPOINT,
          api_key=AZURE_LLM_KEY,
          api_version="2025-01-01-preview",
        ),
        tts=azure.TTS(
          speech_key = AZURE_SPEECH_KEY,
          speech_region = AZURE_SPEECH_REGION,
        ),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )
    assistant = Assistant();
    await session.start(
        room=ctx.room,
        agent=assistant,
        room_input_options=RoomInputOptions(
            # For telephony applications, use `BVCTelephony` instead for best results
            noise_cancellation=noise_cancellation.BVC(), 
            # allow_barge_in=True
        ),
    )

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
