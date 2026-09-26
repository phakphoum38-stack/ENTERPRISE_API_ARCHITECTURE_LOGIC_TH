<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Contracts;

final readonly class RequestContext
{
    public function __construct(
        public string $requestId,
        public string $correlationId,
        public string $actor,
        public string $contractVersion,
    ) {}
}
