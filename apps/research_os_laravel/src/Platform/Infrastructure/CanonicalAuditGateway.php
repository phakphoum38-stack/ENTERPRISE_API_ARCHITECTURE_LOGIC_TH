<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Infrastructure;

use ResearchOS\Platform\Contracts\AuditGateway;
use ResearchOS\Platform\Contracts\RequestContext;
use RuntimeException;

final class CanonicalAuditGateway implements AuditGateway
{
    public function __construct(
        private readonly CanonicalPlatformClient $client,
        private readonly string $endpoint,
    ) {
    }

    public function record(RequestContext $context, array $event): string
    {
        $result = $this->client->post(
            $context,
            $this->endpoint,
            ['event' => $event],
        );

        $auditId = $result['audit_id'] ?? null;
        if (!is_string($auditId) || $auditId === '') {
            throw new RuntimeException('Canonical audit response is invalid.');
        }

        return $auditId;
    }
}
