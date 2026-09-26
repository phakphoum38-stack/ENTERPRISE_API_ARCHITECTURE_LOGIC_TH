<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Contracts;

interface ControlGateway
{
    /** @param array<string, mixed> $command */
    public function execute(RequestContext $context, array $command): array;
}
