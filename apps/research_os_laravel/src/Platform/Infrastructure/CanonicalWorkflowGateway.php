<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Infrastructure;

use ResearchOS\Platform\Contracts\RequestContext;
use ResearchOS\Platform\Contracts\WorkflowGateway;

final class CanonicalWorkflowGateway implements WorkflowGateway
{
    public function __construct(private readonly CanonicalPlatformClient $client)
    {
    }

    public function dispatch(RequestContext $context, string $command, array $payload): array
    {
        return $this->client->post(
            $context,
            (string) config('platform.endpoints.workflow'),
            ['command' => $command, 'payload' => $payload],
        );
    }
}
