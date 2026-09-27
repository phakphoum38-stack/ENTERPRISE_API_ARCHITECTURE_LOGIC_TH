<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Contracts;

interface VersionGateway
{
    public function supports(string $contractVersion): bool;
}
