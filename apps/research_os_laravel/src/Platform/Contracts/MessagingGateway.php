<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Contracts;

interface MessagingGateway
{
    /** @param array<string, mixed> $payload */
    public function publish(RequestContext $context, string $topic, array $payload): string;
}
