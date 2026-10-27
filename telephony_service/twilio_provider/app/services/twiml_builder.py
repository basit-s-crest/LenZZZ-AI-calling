from twilio.twiml.voice_response import VoiceResponse, Connect

def build_stream_twiml(pipecat_ws_url: str) -> str:
    """Returns TwiML that connects the call to a Pipecat WebSocket URL."""
    resp = VoiceResponse()
    connect = Connect()
    connect.stream(url=pipecat_ws_url)
    resp.append(connect)
    resp.say("Sorry, we are having trouble connecting. Goodbye.")
    resp.hangup()
    return str(resp)