<?php
declare(strict_types=1);
namespace ResearchOS\Platform\Infrastructure;
use ResearchOS\Platform\Contracts\VersionGateway;
final class ConfiguredVersionGateway implements VersionGateway {
    public function __construct(private readonly string $supportedMajor = '1') {}
    public function supports(string $contractVersion): bool {
        $major = explode('.', $contractVersion, 2)[0] ?? '';
        return $major !== '' && $major === $this->supportedMajor;
    }
}
