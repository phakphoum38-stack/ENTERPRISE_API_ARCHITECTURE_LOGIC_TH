<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Contracts;

interface WorkflowGateway
{
    /** @return array<string, mixed> */
    public function dispatch(RequestContext $context, string $command, array $payload): array;
}
