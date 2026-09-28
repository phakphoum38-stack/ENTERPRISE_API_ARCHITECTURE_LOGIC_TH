<?php
declare(strict_types=1);
namespace ResearchOS\Platform\Application;
use ResearchOS\Platform\Contracts\VersionGateway;
final class VersionApplicationService {
    public function __construct(private readonly VersionGateway $gateway) {}
    public function supports(string $version): bool { return $this->gateway->supports($version); }
}
