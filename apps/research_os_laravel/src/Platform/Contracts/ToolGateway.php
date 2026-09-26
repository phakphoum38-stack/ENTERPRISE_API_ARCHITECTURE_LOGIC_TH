<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Contracts;

interface ToolGateway
{
    /** @param array<string, mixed> $input */
    public function invoke(RequestContext $context, string $tool, array $input): array;
}
