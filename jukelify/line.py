import json

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    ApiClient,
    Configuration,
    FlexContainer,
    FlexMessage,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)
from linebot.v3.webhooks import MessageEvent, PostbackEvent, TextMessageContent

from jukelify.spotify import spotify_api
from jukelify.utils import LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
line_handler = WebhookHandler(LINE_CHANNEL_SECRET)


@line_handler.add(MessageEvent, message=TextMessageContent)
def handling_message(event: MessageEvent):
    with ApiClient(configuration) as api_client:
        if isinstance(event.message.text, str) and event.message.text.startswith(
            "@Jukelify"
        ):
            line_bot_api = MessagingApi(api_client)

            result = spotify_api.exec(event.message.text)
            if isinstance(result, str):
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=result)],
                    )
                )
            elif isinstance(result, dict):
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            FlexMessage(
                                contents=FlexContainer.from_dict(result),
                                altText="Spotify search result",
                            )
                        ],
                    )
                )


@line_handler.add(PostbackEvent)
def handle_postback(event: PostbackEvent):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        payload = json.loads(event.postback.data)
        spotify_api.add_to_queue(track_name=payload["name"], track_uri=payload["uri"])
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=f"Add {payload['name']} to your queue.")],
            )
        )
