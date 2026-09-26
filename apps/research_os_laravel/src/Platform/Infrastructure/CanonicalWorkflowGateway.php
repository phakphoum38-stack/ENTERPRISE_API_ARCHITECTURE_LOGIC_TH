<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Infrastructure;

use ResearchOS\Platform\Contracts\RequestContext;
use ResearchOS\Platform\Contracts\WorkflowGateway;

final class CanonicalWorkflowGateway implements WorkflowGateway
{
    public function __construct(
        private readonly CanonicalPlatformClient $client,
        private readonly string $endpoint,
    ) {
    }

    public function dispatch(RequestContext $context, string $command, array $payload): array
    {
        return $this->client->post(
            $context,
            $this->endpoint,
            ['command' => $command, 'payload' => $payload],
        );
    }
}
