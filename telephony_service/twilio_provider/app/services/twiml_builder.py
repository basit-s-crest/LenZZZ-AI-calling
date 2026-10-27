from twilio.twiml.voice_response import VoiceResponse, Connect

def build_stream_twiml(
    pipecat_ws_url: str,
    connect_action_url: str | None = None,
    stream_status_url: str | None = None,
) -> str:
    """Returns TwiML that connects the call to a Pipecat WebSocket URL."""
    resp = VoiceResponse()
    connect = Connect(action=connect_action_url) if connect_action_url else Connect()
    connect.stream(
        url=pipecat_ws_url,
        status_callback=stream_status_url if stream_status_url else None,
    )
    resp.append(connect)
    return str(resp)