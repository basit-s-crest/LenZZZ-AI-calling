"""TwiML = the instructions Twilio runs once the callee answers.

For now: speak a message. Later this is where <Connect><Stream> (audio -> AI layer) goes.
"""
from twilio.twiml.voice_response import VoiceResponse


def build_say_twiml(message: str) -> str:
    response = VoiceResponse()
    response.say(message)      # the SDK XML-escapes the text
    return str(response)
