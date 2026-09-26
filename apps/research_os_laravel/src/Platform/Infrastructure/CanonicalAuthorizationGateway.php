<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Infrastructure;

use ResearchOS\Platform\Contracts\AuthorizationDecision;
use ResearchOS\Platform\Contracts\AuthorizationGateway;
use ResearchOS\Platform\Contracts\RequestContext;

final class CanonicalAuthorizationGateway implements AuthorizationGateway
{
    public function __construct(private readonly CanonicalPlatformClient $client)
    {
    }

    public function decide(RequestContext $context, string $capability, string $resource): AuthorizationDecision
    {
        try {
            $result = $this->client->post(
                $context,
                (string) config('platform.endpoints.authorization'),
                ['capability' => $capability, 'resource' => $resource],
            );

            return AuthorizationDecision::tryFrom((string) ($result['decision'] ?? ''))
                ?? AuthorizationDecision::UNKNOWN;
        } catch (\Throwable) {
            return AuthorizationDecision::UNKNOWN;
        }
    }
}
