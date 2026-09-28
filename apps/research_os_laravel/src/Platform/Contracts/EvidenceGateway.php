<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Contracts;

interface EvidenceGateway
{
    /** @param array<string, mixed> $evidence */
    public function record(RequestContext $context, array $evidence): string;
}
