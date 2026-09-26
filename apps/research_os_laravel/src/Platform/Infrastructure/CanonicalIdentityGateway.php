<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Infrastructure;

use ResearchOS\Platform\Contracts\IdentityGateway;
use ResearchOS\Platform\Contracts\RequestContext;
use RuntimeException;

final class CanonicalIdentityGateway implements IdentityGateway
{
    public function __construct(
        private readonly CanonicalPlatformClient $client,
        private readonly string $endpoint,
    ) {
    }

    public function resolve(RequestContext $context): string
    {
        $result = $this->client->post(
            $context,
            $this->endpoint,
            ['actor' => $context->actor],
        );

        $identity = $result['identity'] ?? null;
        if (!is_string($identity) || $identity === '') {
            throw new RuntimeException('Canonical identity response is invalid.');
        }

        return $identity;
    }
}
