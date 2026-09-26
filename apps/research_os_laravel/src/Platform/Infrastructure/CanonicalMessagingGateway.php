<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Infrastructure;

use ResearchOS\Platform\Contracts\MessagingGateway;
use ResearchOS\Platform\Contracts\RequestContext;
use RuntimeException;

final class CanonicalMessagingGateway implements MessagingGateway
{
    public function __construct(private readonly CanonicalPlatformClient $client)
    {
    }

    public function publish(RequestContext $context, string $topic, array $payload): string
    {
        $result = $this->client->post(
            $context,
            (string) config('platform.endpoints.messaging'),
            ['topic' => $topic, 'payload' => $payload],
        );

        $messageId = $result['message_id'] ?? null;
        if (!is_string($messageId) || $messageId === '') {
            throw new RuntimeException('Canonical messaging response is invalid.');
        }

        return $messageId;
    }
}
