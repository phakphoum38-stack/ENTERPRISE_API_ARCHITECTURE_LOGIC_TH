<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Contracts;

interface OperationsGateway
{
    /** @return array<string, mixed> */
    public function snapshot(): array;
}
