<?php

declare(strict_types=1);

namespace ResearchOS\Platform\Infrastructure;

use Illuminate\Http\Client\Factory;
use Illuminate\Http\Client\PendingRequest;
use Closure;
use ResearchOS\Platform\Contracts\RequestContext;
use RuntimeException;

final class CanonicalPlatformClient
{
    public function __construct(
        private readonly Factory $http,
        private readonly string $baseUrl,
        private readonly float $timeout = 10.0,
        private readonly float $connectTimeout = 3.0,
        private readonly ?Closure $transport = null,
    ) {
    }

    /** @param array<string, mixed> $payload */
    public function post(RequestContext $context, string $endpoint, array $payload): array
    {
        $baseUrl = rtrim($this->baseUrl, '/');
        if ($baseUrl === '') {
            throw new RuntimeException('Canonical Research OS Platform URL is not configured.');
        }

        if ($this->transport !== null) {
            $result = ($this->transport)($context, $endpoint, $payload);
            if (!is_array($result)) {
                throw new RuntimeException('Canonical Research OS Platform test transport returned a non-object response.');
            }
            return $result;
        }

        $response = $this->request($context)->post($baseUrl.$endpoint, $payload);
        $response->throw();

        $json = $response->json();
        if (!is_array($json)) {
            throw new RuntimeException('Canonical Research OS Platform returned a non-object response.');
        }

        return $json;
    }

    private function request(RequestContext $context): PendingRequest
    {
        return $this->http
            ->acceptJson()
            ->asJson()
            ->timeout($this->timeout)
            ->connectTimeout($this->connectTimeout)
            ->withHeaders([
                'X-Request-Id' => $context->requestId,
                'X-Correlation-Id' => $context->correlationId,
                'X-Contract-Version' => $context->contractVersion,
                'X-Actor' => $context->actor,
                'Idempotency-Key' => $context->requestId,
            ]);
    }
}
