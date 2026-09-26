<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Contracts;

interface AuditGateway
{
    /** @param array<string, mixed> $event */
    public function record(RequestContext $context, array $event): string;
}
