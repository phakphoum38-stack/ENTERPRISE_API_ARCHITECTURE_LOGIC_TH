<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Infrastructure;

use ResearchOS\Platform\Contracts\EvidenceGateway;
use ResearchOS\Platform\Contracts\RequestContext;
use RuntimeException;

final class CanonicalEvidenceGateway implements EvidenceGateway
{
    public function __construct(
        private readonly CanonicalPlatformClient $client,
        private readonly string $endpoint,
    ) {
    }

    public function record(RequestContext $context, array $evidence): string
    {
        $result = $this->client->post(
            $context,
            $this->endpoint,
            ['evidence' => $evidence],
        );

        $evidenceId = $result['evidence_id'] ?? null;
        if (!is_string($evidenceId) || $evidenceId === '') {
            throw new RuntimeException('Canonical evidence response is invalid.');
        }

        return $evidenceId;
    }
}
