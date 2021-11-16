build:
	docker build --no-cache -t humorwang/tg-channel-monitor:v1.0 .
tag:
	docker tag humorwang/tg-channel-monitor:v1.0  humorwang/tg-channel-monitor:latest
push:
	docker push humorwang/tg-channel-monitor:latest

